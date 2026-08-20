#!/usr/bin/env python3
"""Evaluate an isolated Candidate against correctness and empirical evidence.

Implements the Evaluation Gate from ``docs/process/evidence-cycle.md``:

    keep iff checks.sh passes
         AND no HARD_GATE/TARGET/OPTIMIZATION metric regresses beyond tolerance
         AND telemetry does not contradict itself

measure.sh may emit either a single-metric payload (unchanged, legacy shape)
or a multi-metric payload with a top-level "metrics" list, each entry
optionally tiered via "tier": "hard_gate" | "target" | "optimization" |
"observation" (default hard_gate). Both paths are evaluated through the same
keep/revert rule - see baseline.evaluate_candidate.

Every outcome is appended to ``.recurspec/evidence/<module>/log.jsonl``. A regression
emits Empirical Feedback. Every revert also records a Negative Pattern so repairs do not
retry an invalidated approach. Bounded retry counts escalate to human judgment.
"""

from __future__ import annotations

import json
import ntpath
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

from .evidence import log_event
from .metrics import (
    REGRESSED,
    UNKNOWN,
    Comparison,
    compare,
    count_consecutive_reverts,
    count_total_reverts,
    evaluate_candidate,
    find_baseline,
    parse_measurement,
    read_negative_patterns,
    resolve_tier,
    telemetry_contradiction,
)
from .spec_runner.workers import MergeAuthorization

KEEP, REVERT, ERROR, ESCALATE = 0, 1, 2, 3


class CandidateLifecycleError(RuntimeError):
    """The Candidate could not be isolated, merged, or disposed safely."""


_MODULE_NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]*$")

# Recurspec's own generated runtime state - never anything a project chose to track.
_RUNTIME_STATE_RE = re.compile(
    r"^\.recurspec/(?:evidence/[^/]+/log\.jsonl|handoffs/.*|worker-authorizations\.json|frontiers/.*)$"
)


def _is_ignorable_runtime_state(status_line: str) -> bool:
    """True iff a ``git status --porcelain`` line is Recurspec's own untracked,
    generated runtime state - never a tracked file, no matter where it lives.

    A blanket ``:(exclude).recurspec/`` pathspec would also hide a *tracked* dirty
    file a project deliberately committed under ``.recurspec/`` (e.g. a checked-in
    config); only an untracked path matching Recurspec's own known-generated shapes is
    safe to ignore here.
    """
    if len(status_line) < 4 or status_line[:2] != "??":
        return False
    path = status_line[3:]
    if path.startswith('"'):
        # A quoted (unusually-charactered) path cannot be safely pattern-matched;
        # fail closed rather than risk ignoring something unexpected.
        return False
    return bool(_RUNTIME_STATE_RE.match(path))


def _validate_module_name(module: str) -> None:
    """Reject anything but a single safe path segment.

    ``module`` is interpolated straight into probe and evidence paths; a value
    containing ``/``, ``\\``, ``..``, or an absolute path could point those reads and
    writes outside ``modules/<module>`` and ``.recurspec/evidence/<module>``.
    """
    if not _MODULE_NAME_RE.match(module):
        raise CandidateLifecycleError(
            f"module name {module!r} is not a single safe path segment"
        )


_GIT_EXE: str | None = None


def _git_executable() -> str:
    """Resolve ``git`` to an absolute path once so every invocation below is immune to
    a PATH-order hijack instead of trusting whichever ``git`` a manipulated PATH
    resolves first."""
    global _GIT_EXE
    if _GIT_EXE is None:
        resolved = shutil.which("git")
        if resolved is None:
            raise CandidateLifecycleError("git is not on PATH")
        _GIT_EXE = resolved
    return _GIT_EXE


def _git(repo: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(  # noqa: S603 - git resolved to an absolute path above; args are internal, not shell-interpreted
        [_git_executable(), "-C", str(repo), *args],
        capture_output=True,
        text=True,
    )
    if check and result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip() or f"exit {result.returncode}"
        raise CandidateLifecycleError(f"git {' '.join(args)} failed: {detail}")
    return result


def _snapshot_tree(root: Path) -> dict[str, bytes]:
    """Read every regular file under ``root`` into {posix-relative-path: bytes}."""
    snapshot: dict[str, bytes] = {}
    if not root.is_dir():
        return snapshot
    for path in root.rglob("*"):
        if path.is_file():
            snapshot[path.relative_to(root).as_posix()] = path.read_bytes()
    return snapshot


def _materialize_tree(root: Path, snapshot: dict[str, bytes]) -> None:
    """Replace everything under ``root`` with exactly the given snapshot."""
    if root.exists():
        shutil.rmtree(root)
    for relative, content in snapshot.items():
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)


_TRUSTED_TREES = ("tests", "modules", "scripts")
_TRUSTED_FILES = (
    "conftest.py",
    "pytest.ini",
    "pyproject.toml",
    "ruff.toml",
    ".ruff.toml",
    "setup.cfg",
    "tox.ini",
    "sitecustomize.py",
    "usercustomize.py",
)
# Optional, baseline-only declaration of additional probe-adjacent inputs a project
# needs pinned that the fixed lists above cannot anticipate (R-640): a project-specific
# helper under scripts/, a plugin config, etc. Never read from the Candidate worktree -
# a Candidate could otherwise grant itself trust by editing the manifest.
_TRUSTED_MANIFEST = ".recurspec/trusted-inputs.json"


def _validate_trusted_manifest_entry(entry: str) -> str:
    """Reject anything but a clean repository-relative path (R-640): the same escape
    shapes `_validate_module_name` blocks for `module` apply here to manifest entries."""
    if not isinstance(entry, str) or not entry or entry != entry.strip():
        raise CandidateLifecycleError(
            f"{_TRUSTED_MANIFEST} entry {entry!r} is not a clean relative path"
        )
    posix = entry.replace("\\", "/")
    if posix.startswith("/") or posix.startswith("~") or ntpath.splitdrive(entry)[0]:
        raise CandidateLifecycleError(
            f"{_TRUSTED_MANIFEST} entry {entry!r} must be repository-relative"
        )
    parts = posix.split("/")
    if any(part in ("", ".", "..") for part in parts):
        raise CandidateLifecycleError(
            f"{_TRUSTED_MANIFEST} entry {entry!r} must not contain '..' or empty segments"
        )
    return posix


def _load_trusted_manifest(baseline: Path) -> tuple[str, ...]:
    """Read the optional trusted-input manifest from the baseline (R-640).

    Absent is the common case and pins nothing extra. Present-but-malformed fails
    closed - a manifest that cannot be trusted must never be silently skipped, which
    would quietly narrow the trust boundary a project explicitly declared.
    """
    manifest_path = baseline / _TRUSTED_MANIFEST
    if not manifest_path.is_file():
        return ()
    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise CandidateLifecycleError(f"could not read {_TRUSTED_MANIFEST}: {exc}") from exc
    if not isinstance(payload, dict) or not isinstance(payload.get("paths"), list):
        raise CandidateLifecycleError(
            f"{_TRUSTED_MANIFEST} must be a JSON object with a 'paths' array"
        )
    return tuple(_validate_trusted_manifest_entry(entry) for entry in payload["paths"])


def _pin_trusted_probe_inputs(baseline: Path, worktree: Path) -> tuple[str, ...]:
    """Copy the trusted probe environment from baseline into the Candidate worktree.

    checks.sh/measure.sh are not the full judge: they source helpers under modules/,
    run tests/, and honor root pytest/ruff config. A Candidate must not control any
    of those. Returns the manifest paths pinned so the caller can
    restore them the same way after evaluation.
    """
    for name in _TRUSTED_TREES:
        source = baseline / name
        if source.is_dir():
            _materialize_tree(worktree / name, _snapshot_tree(source))
    for name in _TRUSTED_FILES:
        source = baseline / name
        destination = worktree / name
        if source.is_file():
            destination.write_bytes(source.read_bytes())
        elif destination.exists() or destination.is_symlink():
            destination.unlink()
    manifest_paths = _load_trusted_manifest(baseline)
    for rel in manifest_paths:
        source = baseline / rel
        destination = worktree / rel
        if source.is_dir():
            _materialize_tree(destination, _snapshot_tree(source))
        elif source.is_file():
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(source.read_bytes())
        elif destination.is_dir():
            shutil.rmtree(destination)
        elif destination.exists() or destination.is_symlink():
            destination.unlink()
    return manifest_paths


def _bash(platform: str | None = None) -> str | None:
    override = os.environ.get("RECURSPEC_BASH")
    if override:
        return override if os.path.isfile(override) else shutil.which(override)

    # On Windows, PATH commonly resolves `bash` to the WSL launcher even when
    # no distro is installed. Prefer the Bash shipped beside Git for Windows.
    if (platform or os.name) == "nt":
        git = shutil.which("git")
        if git:
            git_root = ntpath.dirname(ntpath.dirname(git))
            for candidate in (
                ntpath.join(git_root, "bin", "bash.exe"),
                ntpath.join(git_root, "usr", "bin", "bash.exe"),
            ):
                if os.path.isfile(candidate):
                    return candidate

    return shutil.which("bash")


def run_script(
    script_path: str,
    module: str,
    timeout: int = 300,
    cwd: str | os.PathLike[str] | None = None,
) -> tuple[int, str, str]:
    """Run an evaluation script, returning ``(returncode, stdout, stderr)``.

    stdout and stderr are kept separate: the measurement payload is parsed from
    stdout alone, so diagnostics on stderr cannot corrupt it.
    """
    resolved_script = os.path.join(os.fspath(cwd), script_path) if cwd is not None else script_path
    if not os.path.exists(resolved_script):
        return 127, "", f"Script not found: {script_path}"
    bash = _bash()
    if bash is None:
        return 127, "", "No `bash` on PATH; evaluation scripts require a POSIX shell."
    try:
        env = os.environ.copy()
        env["RECURSPEC_PYTHON"] = sys.executable
        res = subprocess.run(  # noqa: S603 - bash resolved to an absolute path above; script_path is a pre-validated file, no shell
            [bash, script_path, module],
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=cwd,
            env=env,
        )
        return res.returncode, res.stdout, res.stderr
    except subprocess.TimeoutExpired:
        return 124, "", f"Timed out after {timeout}s: {script_path}"
    except OSError as e:
        return 126, "", f"Could not execute {script_path}: {e}"


def _sub_metric_comparisons(
    module: str,
    entries: list[dict[str, Any]],
    tolerance_pct: float,
    baseline_branch: str,
    log_dir: str,
) -> list[tuple[str, Comparison, str]]:
    """Resolve each multi-metric payload entry against its own trunk baseline."""
    out: list[tuple[str, Comparison, str]] = []
    for entry in entries:
        name = entry.get("metric", "unknown_metric")
        tier = resolve_tier(entry.get("tier"))
        base_event = find_baseline(module, name, log_dir, baseline_branch)
        base_value = base_event["metrics"].get("value") if base_event else None
        cmp_result = compare(
            name,
            entry.get("value"),
            base_value,
            tolerance_pct=tolerance_pct,
            declared_direction=entry.get("direction"),
        )
        out.append((name, cmp_result, tier))
    return out


def evaluate_change(
    module: str,
    candidate_branch: str,
    tolerance_pct: float = 20.0,
    baseline_branch: str = "main",
    log_dir: str = ".recurspec/evidence",
    record_baseline: bool = False,
    stagnation_limit: int = 5,
    attempt_ceiling: int = 8,
    work_dir: str | os.PathLike[str] | None = None,
) -> tuple[int, str]:
    _validate_module_name(module)
    if record_baseline and candidate_branch != baseline_branch:
        raise ValueError(
            "baseline promotion requires evaluation on the baseline branch after merge"
        )

    checks_path = os.path.join("modules", module, "checks.sh")
    measure_path = os.path.join("modules", module, "measure.sh")

    def record(event_type, metrics, stage, verdict=None, reason=None, branch=None):
        log_event(
            module,
            event_type,
            metrics,
            evidence_stage=stage,
            branch=branch or candidate_branch,
            verdict=verdict,
            reason=reason,
            log_dir=log_dir,
        )

    def revert(reason: str) -> tuple[int, str]:
        """Common exit for every revert path: log the negative pattern, then
        decide REVERT vs ESCALATE from the bounded retry counts."""
        record("negative_pattern", {}, "Refuted", "revert", reason)
        streak = count_consecutive_reverts(module, log_dir, branch=candidate_branch)
        attempts = count_total_reverts(module, log_dir, branch=candidate_branch)
        if attempts >= attempt_ceiling:
            print(
                f"[ESCALATE] attempt ceiling ({attempt_ceiling}) reached on "
                f"{candidate_branch}; needs a human decision."
            )
            return ESCALATE, f"attempt ceiling reached: {reason}"
        if streak >= stagnation_limit:
            print(
                f"[ESCALATE] {streak} consecutive reverts on {candidate_branch}, "
                "no forward progress; needs a human decision."
            )
            return ESCALATE, f"stagnation ({streak} reverts): {reason}"
        return REVERT, reason

    print(f"=== EVALUATING {module} @ {candidate_branch} ===")

    prior = read_negative_patterns(module, log_dir)
    prior_here = [e for e in prior if e.get("branch") == candidate_branch]
    if prior_here:
        print(
            f"[NEGATIVE PATTERNS] {len(prior_here)} prior reverted attempt(s) on this "
            "branch - read before proposing another change:"
        )
        for e in prior_here[-5:]:
            print(f"  - {e.get('ts', '?')}: {e.get('reason', '(no reason recorded)')}")

    # 1. Correctness backpressure. Non-negotiable and always first: a metric
    #    improvement on incorrect code is not an improvement.
    code, out, err = run_script(checks_path, module, cwd=work_dir)
    if code != 0:
        detail = (err or out).strip()
        print(f"[REVERT] checks.sh FAILED (exit {code})\n{detail}")
        record("decision", {}, "Refuted", "revert", f"checks.sh failed (exit {code})")
        return revert("checks.sh failed")
    print("[PASS] correctness backpressure green")

    # 2. Measurement.
    code, out, err = run_script(measure_path, module, cwd=work_dir)
    if code != 0:
        detail = (err or out).strip()
        print(f"[REVERT] measure.sh FAILED (exit {code})\n{detail}")
        record("decision", {}, "Refuted", "revert", f"measure.sh failed (exit {code})")
        return revert("measure.sh failed")

    try:
        payload = parse_measurement(out)
    except ValueError as e:
        # Unparseable output is an instrument failure, never a pass. The old
        # behaviour substituted value=0 here, which reads as a perfect score
        # for any lower-is-better metric.
        print(f"[REVERT] unusable measure.sh output: {e}")
        record("decision", {}, "Unknown", "revert", f"unparseable measurement: {e}")
        return revert("unparseable measurement")

    contradiction = telemetry_contradiction(payload)
    if contradiction:
        print(f"[REVERT] telemetry contradiction: {contradiction}")
        record(
            "decision", payload, "Unknown", "revert", f"telemetry contradiction: {contradiction}"
        )
        return revert("telemetry contradiction")

    entries = payload.get("metrics")
    if isinstance(entries, list) and entries:
        # --- Multi-metric, tiered path -----------------------------------
        for entry in entries:
            m = entry.get("metric", "unknown_metric")
            tier = entry.get("tier", "hard_gate")
            print(
                f"[MEASURED] {m} = {entry.get('value')} {entry.get('unit', '')} "
                f"(tier={tier})".rstrip()
            )
        record("candidate", payload, "Measured")

        triples = _sub_metric_comparisons(module, entries, tolerance_pct, baseline_branch, log_dir)
        for name, cmp_result, tier in triples:
            print(
                f"[BASELINE] {name} ({tier}): {cmp_result.baseline} -> "
                f"{cmp_result.current} :: {cmp_result.verdict.upper()} "
                f"({cmp_result.reason})"
            )
            if cmp_result.verdict == REGRESSED:
                record(
                    "signal_d",
                    {
                        "metric": name,
                        "tier": tier,
                        "current": cmp_result.current,
                        "baseline": cmp_result.baseline,
                        "delta_pct": cmp_result.delta_pct,
                    },
                    "Measured",
                    reason=cmp_result.reason,
                )

        dominance = evaluate_candidate(triples)
        if not dominance.accepted:
            print(f"[REVERT] {dominance.reason}")
            record("decision", payload, "Measured", "revert", dominance.reason)
            return revert(dominance.reason)

        record("decision", payload, "Measured", "keep", dominance.reason)
        if record_baseline:
            for entry in entries:
                record("baseline", entry, "Measured", branch=baseline_branch)
            print(f"[BASELINE] promoted {len(entries)} metric(s) on {baseline_branch}")
        print(f"[KEEP] {candidate_branch} authorized for merge ({dominance.reason})")
        return KEEP, dominance.reason

    # --- Legacy single-metric path ---------------------------------------
    metric = payload.get("metric", "unknown_metric")
    print(f"[MEASURED] {metric} = {payload.get('value')} {payload.get('unit', '')}".rstrip())
    record("candidate", payload, "Measured")

    base_event = find_baseline(module, metric, log_dir, baseline_branch)
    base_value = base_event["metrics"].get("value") if base_event else None

    cmp_result: Comparison = compare(
        metric,
        payload.get("value"),
        base_value,
        tolerance_pct=tolerance_pct,
        declared_direction=payload.get("direction"),
    )

    base_str = "none" if base_value is None else f"{base_value}"
    print(
        f"[BASELINE] {base_str} -> {cmp_result.current} :: "
        f"{cmp_result.verdict.upper()} ({cmp_result.reason})"
    )

    if cmp_result.verdict == REGRESSED:
        record(
            "signal_d",
            {**payload, "baseline": base_value, "delta_pct": cmp_result.delta_pct},
            "Measured",
            "revert",
            cmp_result.reason,
        )
        print(
            "[REVERT] empirical feedback logged; resolve the Research Frontier before "
            "retrying this leaf."
        )
        return revert(cmp_result.reason)

    if cmp_result.verdict == UNKNOWN:
        record("decision", payload, "Unknown", "revert", cmp_result.reason)
        print(f"[REVERT] undecidable comparison: {cmp_result.reason}")
        return revert(cmp_result.reason)

    record(
        "decision",
        {**payload, "baseline": base_value, "delta_pct": cmp_result.delta_pct},
        "Measured",
        "keep",
        cmp_result.reason,
    )
    if record_baseline:
        # Promote to the trunk baseline only on explicit instruction, after the
        # Outer Loop has actually merged the worktree.
        record("baseline", payload, "Measured", branch=baseline_branch)
        print(f"[BASELINE] promoted {metric}={payload.get('value')} on {baseline_branch}")

    print(f"[KEEP] {candidate_branch} authorized for merge ({cmp_result.reason})")
    return KEEP, cmp_result.reason


def evaluate_isolated_candidate(
    repo: str | os.PathLike[str],
    module: str,
    candidate_branch: str,
    *,
    authorization: MergeAuthorization,
    tolerance_pct: float = 20.0,
    baseline_branch: str = "main",
    log_dir: str | os.PathLike[str] = ".recurspec/evidence",
    record_baseline: bool = False,
    stagnation_limit: int = 5,
    attempt_ceiling: int = 8,
) -> tuple[int, str]:
    """Evaluate one existing Candidate branch in a disposable git worktree.

    A KEEP fast-forwards the checked-out baseline branch. Other decisions leave it
    untouched. Evidence is written to the baseline worktree so disposal cannot erase it.
    Explicit baseline promotion is a second evaluation after the merge.
    """
    _validate_module_name(module)
    maker_id = authorization.maker_id
    checker_id = authorization.checker_id
    if candidate_branch != authorization.candidate_branch:
        raise CandidateLifecycleError(
            "Worker Pool authorization node does not match the Candidate branch"
        )

    requested_repo = Path(repo).resolve()
    top_level = _git(requested_repo, "rev-parse", "--show-toplevel").stdout.strip()
    repo_path = Path(top_level).resolve()

    if candidate_branch == baseline_branch:
        raise CandidateLifecycleError("candidate branch must differ from the baseline branch")
    current_branch = _git(repo_path, "branch", "--show-current").stdout.strip()
    if current_branch != baseline_branch:
        raise CandidateLifecycleError(
            f"baseline branch {baseline_branch!r} must be checked out; found {current_branch!r}"
        )
    # Recurspec's own runtime state (evidence logs, worker authorizations, handoffs)
    # lives under .recurspec/ in the checked-out worktree. A correctly generated
    # prerequisite - e.g. the documented --worker-state path - must never itself block
    # the documented workflow just because a project's .gitignore hasn't caught up
    # Filter it out line by line rather than pathspec-excluding the whole
    # .recurspec/ directory: a blanket exclude would also hide a *tracked* dirty file a
    # project deliberately committed there, which must still block evaluation.
    # --untracked-files=all: without it, git collapses a wholly-untracked directory into
    # one "?? .recurspec/" line instead of listing the files inside, which would defeat
    # per-path matching against _RUNTIME_STATE_RE below.
    dirty_lines = [
        line
        for line in _git(
            repo_path, "status", "--porcelain", "--untracked-files=all"
        ).stdout.splitlines()
        if line.strip() and not _is_ignorable_runtime_state(line)
    ]
    if dirty_lines:
        raise CandidateLifecycleError("baseline worktree must be clean before candidate evaluation")

    baseline_ref = f"refs/heads/{baseline_branch}"
    candidate_ref = f"refs/heads/{candidate_branch}"
    baseline_oid = _git(repo_path, "rev-parse", "--verify", baseline_ref).stdout.strip()
    candidate_oid = _git(repo_path, "rev-parse", "--verify", candidate_ref).stdout.strip()
    if candidate_oid != authorization.candidate_oid:
        raise CandidateLifecycleError(
            "Worker Pool authorization commit does not match the Candidate branch tip"
        )
    ancestry = _git(
        repo_path, "merge-base", "--is-ancestor", baseline_oid, candidate_oid, check=False
    )
    if ancestry.returncode:
        raise CandidateLifecycleError(
            f"candidate {candidate_branch!r} cannot fast-forward {baseline_branch!r}"
        )

    evidence_path = Path(log_dir)
    if not evidence_path.is_absolute():
        evidence_path = repo_path / evidence_path
    evidence_path = evidence_path.resolve()

    # Probe definitions decide keep/revert, so a Candidate must never be able to supply
    # its own checks.sh/measure.sh: the trusted baseline's copies are pinned into the
    # worktree below. Refuse rather than fall back to trusting the Candidate.
    checks_rel = os.path.join("modules", module, "checks.sh")
    measure_rel = os.path.join("modules", module, "measure.sh")
    trusted_checks = repo_path / checks_rel
    trusted_measure = repo_path / measure_rel
    if not trusted_checks.is_file() or not trusted_measure.is_file():
        raise CandidateLifecycleError(
            f"no trusted baseline probe for module {module!r} on {baseline_branch!r}; "
            "refusing to evaluate against Candidate-controlled evaluation scripts"
        )
    # A previous interrupted process may have deleted its directory before unregistering
    # it. Prune only missing worktrees so the Candidate branch can be isolated again.
    _git(repo_path, "worktree", "prune", "--expire", "now")

    temp_root = Path(tempfile.mkdtemp(prefix="recurspec-candidate-"))
    worktree = temp_root / "worktree"
    created = False
    try:
        # Pinned to the verified oid (detached), not the branch name: a branch-name
        # checkout re-resolves at execution time, leaving a window where a concurrent
        # push moves the branch between the rev-parse verify above and this checkout,
        # so evaluation would run against unauthorized code before the later oid
        # re-check (which only guards the merge, not the evaluation already logged).
        _git(repo_path, "worktree", "add", "--quiet", str(worktree), candidate_oid)
        created = True
        log_event(
            module,
            "merge_authorization",
            {"maker_id": maker_id, "checker_id": checker_id},
            evidence_stage="Observed",
            branch=candidate_branch,
            log_dir=str(evidence_path),
        )
        # Trusted logic, Candidate source under test. Restored below so the post-eval
        # dirtiness check reflects only what the Candidate itself committed.
        manifest_paths = _pin_trusted_probe_inputs(repo_path, worktree)
        try:
            code, reason = evaluate_change(
                module,
                candidate_branch,
                tolerance_pct=tolerance_pct,
                baseline_branch=baseline_branch,
                log_dir=str(evidence_path),
                record_baseline=False,
                stagnation_limit=stagnation_limit,
                attempt_ceiling=attempt_ceiling,
                work_dir=worktree,
            )
        finally:
            if worktree.exists():
                restore = (
                    *_TRUSTED_TREES,
                    *_TRUSTED_FILES,
                    *manifest_paths,
                    checks_rel,
                    measure_rel,
                )
                _git(worktree, "checkout", "--force", "--", *restore, check=False)
                _git(worktree, "clean", "-fd", "--", *_TRUSTED_TREES, *manifest_paths, check=False)
                for name in (*_TRUSTED_FILES, *manifest_paths):
                    tracked = _git(worktree, "ls-files", "--", name, check=False)
                    if not tracked.stdout.strip():
                        leftover = worktree / name
                        if leftover.is_file() or leftover.is_symlink():
                            leftover.unlink()
                        elif leftover.is_dir():
                            shutil.rmtree(leftover, ignore_errors=True)
        if code != KEEP:
            return code, reason
        if _git(worktree, "status", "--porcelain").stdout.strip():
            raise CandidateLifecycleError(
                "evaluation probes modified the Candidate worktree; refusing to merge "
                "a commit different from the evaluated tree"
            )

        if _git(repo_path, "rev-parse", baseline_ref).stdout.strip() != baseline_oid:
            raise CandidateLifecycleError("baseline branch moved during candidate evaluation")
        if _git(repo_path, "rev-parse", candidate_ref).stdout.strip() != candidate_oid:
            raise CandidateLifecycleError("candidate branch moved during candidate evaluation")
        _git(repo_path, "merge", "--ff-only", candidate_branch)

        if record_baseline:
            promoted_code, promoted_reason = evaluate_change(
                module,
                baseline_branch,
                tolerance_pct=tolerance_pct,
                baseline_branch=baseline_branch,
                log_dir=str(evidence_path),
                record_baseline=True,
                stagnation_limit=stagnation_limit,
                attempt_ceiling=attempt_ceiling,
                work_dir=repo_path,
            )
            if promoted_code != KEEP:
                raise CandidateLifecycleError(
                    "candidate merged, but post-merge baseline promotion failed: "
                    f"{promoted_reason}"
                )
        return code, reason
    finally:
        try:
            if created:
                removed = _git(
                    repo_path, "worktree", "remove", "--force", str(worktree), check=False
                )
                if removed.returncode != 0:
                    shutil.rmtree(worktree, ignore_errors=True)
        finally:
            shutil.rmtree(temp_root, ignore_errors=True)
            # Covers a partially successful `worktree add` and a failed `remove` after
            # the directory has gone. Git prunes only registrations whose paths vanish.
            _git(repo_path, "worktree", "prune", "--expire", "now")
