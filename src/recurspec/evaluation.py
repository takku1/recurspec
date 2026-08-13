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

import ntpath
import os
import shutil
import subprocess
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


def _git(repo: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True,
        text=True,
    )
    if check and result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip() or f"exit {result.returncode}"
        raise CandidateLifecycleError(f"git {' '.join(args)} failed: {detail}")
    return result


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
        res = subprocess.run(
            [bash, script_path, module],
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=cwd,
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
    if _git(repo_path, "status", "--porcelain").stdout.strip():
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

    # A previous interrupted process may have deleted its directory before unregistering
    # it. Prune only missing worktrees so the Candidate branch can be isolated again.
    _git(repo_path, "worktree", "prune", "--expire", "now")

    temp_root = Path(tempfile.mkdtemp(prefix="recurspec-candidate-"))
    worktree = temp_root / "worktree"
    created = False
    try:
        _git(repo_path, "worktree", "add", "--quiet", str(worktree), candidate_branch)
        created = True
        log_event(
            module,
            "merge_authorization",
            {"maker_id": maker_id, "checker_id": checker_id},
            evidence_stage="Observed",
            branch=candidate_branch,
            log_dir=str(evidence_path),
        )
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
