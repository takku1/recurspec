"""Case-study pair apparatus for the pre-registered R-400–R-403 protocol."""

from __future__ import annotations

import re
import secrets
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DEFAULT_PAIR_DIR = "docs/research/pairs"
PROTOCOL_DATE = "2026-08-14"
ASSIGNED_RE = re.compile(
    r"^- Assignment method \(coin flip / first-picked\) and result:\s*(.*?)\s*$",
    re.MULTILINE,
)
UNASSIGNED = "unassigned"
_TICKET_ID_RE = re.compile(r"\b[A-Z]+(?:-[A-Z]+)*-\d+\b")
_ARM_START_SECTION = re.compile(
    r"(?P<heading>^## Arm start[^\n]*\n)(?P<body>.*?)(?=^## |\Z)",
    re.MULTILINE | re.DOTALL,
)
_ARM_LABEL = {"recurspec": "Recurspec arm", "baseline": "Baseline arm"}
VERIFY_TIMEOUT_SECONDS = 1800
OUTPUT_TAIL_CHARS = 2000
_ACCEPTED_NO_RE = re.compile(
    r"^- Accepted implementation: no\.[^\n]*$",
    re.MULTILINE,
)


class StudyInstrumentError(RuntimeError):
    """The study command could not create or assign a pair log."""


@dataclass(frozen=True)
class StudyPair:
    pair_id: str
    path: str
    project: str
    assigned: bool
    assignment: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "assigned": self.assigned,
            "assignment": self.assignment,
            "pair_id": self.pair_id,
            "path": self.path,
            "project": self.project,
        }


@dataclass(frozen=True)
class AcceptResult:
    arm: str
    checker: str
    maker: str
    verify_command: str
    exit_code: int
    timestamp: str
    output_tail: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "arm": self.arm,
            "checker": self.checker,
            "exit_code": self.exit_code,
            "maker": self.maker,
            "output_tail": self.output_tail,
            "timestamp": self.timestamp,
            "verify_command": self.verify_command,
        }


def is_recurspec_repository(path: str | Path) -> bool:
    pyproject = Path(path) / "pyproject.toml"
    if not pyproject.is_file():
        return False
    try:
        text = pyproject.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return False
    return bool(re.search(r'(?m)^name\s*=\s*"recurspec"\s*$', text))


def _reject_table_unsafe(label: str, value: str) -> None:
    """A ``|`` or newline in a value bound for a single-line Markdown table cell would
    corrupt the row and break every later regex-based read/rewrite of it (``assign_pair``,
    ``_parse_pending_tasks``) - refuse up front rather than write an unrecoverable log."""
    if "|" in value or "\n" in value:
        raise StudyInstrumentError(
            f"{label} must not contain '|' or a newline (breaks the pair log table): {value!r}"
        )


def _render_log(
    *,
    pair_id: str,
    project: str,
    task_a: str,
    task_b: str,
    hours: str,
    baseline: str,
) -> str:
    return (
        "# Case-study decision log (R-400–R-403)\n\n"
        "Use one copy of this file per matched task pair. Fill it **before** either "
        "task starts, except the outcome rows. Do not invent numbers. If a field is "
        "unknown, write `unknown` — never a default metric.\n\n"
        "This is apparatus, not results. Recurspec's own repository is excluded from "
        "the task population "
        "([evaluation-protocol.md](../evaluation-protocol.md) §2).\n\n"
        "## Pre-registration binding\n\n"
        f"- Protocol version / date: {PROTOCOL_DATE}\n"
        f"- Pair id: `{pair_id}`\n"
        f"- Project (not recurspec itself): `{project}`\n"
        f"- Assignment method (coin flip / first-picked) and result: {UNASSIGNED}\n"
        f"- A-priori time estimate for each task (set before either starts): {hours}\n\n"
        "## Tasks\n\n"
        "| Arm | Task name | Scope estimate | Condition |\n"
        "|---|---|---|---|\n"
        f"| Pending-A | {task_a} | {hours} | unassigned |\n"
        f"| Pending-B | {task_b} | {hours} | unassigned |\n\n"
        "## Baseline workflow (as it really is)\n\n"
        f"{baseline}\n\n"
        "## Outcomes (fill only as observed)\n\n"
        "| Measure | Recurspec arm | Baseline arm | Source |\n"
        "|---|---|---|---|\n"
        "| Wall-clock to first accepted implementation | unknown | unknown | |\n"
        "| Review round-trips | unknown | unknown | |\n"
        "| Reverted or redone work | unknown | unknown | |\n"
        "| Structure-Gate diagnostics caught before merge | unknown | n/a | |\n"
        "| Escaped mismatches within 30 days | unknown | unknown | |\n"
        "| Decision Class later reversed? cost? | unknown | unknown | |\n"
        "| Repeated a previously-failed approach? | unknown | n/a | |\n"
        "| Failed-to-help? (2× time or tree abandoned) | unknown | unknown | |\n\n"
        "## Manual Evaluation Gate overrides\n\n"
        "| When | Gate would have | Human did | Reason |\n"
        "|---|---|---|---|\n\n"
        "## Arm start (observed, not a-priori)\n\n"
        "- Recurspec arm started: not started\n"
        "- Baseline arm started: not started\n"
        "- Accepted implementation: no. Do not fill wall-clock until an independent accept.\n\n"
        "## Post-hoc metrics\n\n"
        "List any number reported that is not in the protocol §5 table. "
        "Label each `post-hoc`.\n"
    )


def _ticket_ids(*texts: str) -> list[str]:
    ids: list[str] = []
    for text in texts:
        for match in _TICKET_ID_RE.finditer(text):
            if match.group(0) not in ids:
                ids.append(match.group(0))
    return ids


def _tracked_markdown(project: Path) -> list[Path]:
    """Best-effort scan of a subject project's own incomplete-work trackers.

    Not a full Contract Tree parse (the subject project may not have one) --
    mirrors ``is_recurspec_repository``'s lightweight-scan style. Root-level
    ``.md`` files plus everything under ``docs/`` covers the common tracker
    locations (``ROADMAP.md``, ``docs/open-work.md``, and similar) without
    walking the whole tree.
    """
    found: list[Path] = []
    if project.is_dir():
        found.extend(sorted(project.glob("*.md")))
        docs = project / "docs"
        if docs.is_dir():
            found.extend(sorted(docs.rglob("*.md")))
    return found


def check_contamination(project: str | Path, task_a: str, task_b: str) -> list[str]:
    """Return contamination findings for either task's ticket id in ``project``.

    A matched pair's baseline arm must be the project's plain, pre-existing
    workflow; a Recurspec arm's own ticket must not already have been worked
    before the pair is assigned. Both fail the same way: an id that already
    has Recurspec fingerprints in the subject repository. Returns one
    human-readable finding per (id, location) hit; empty means clean.
    """
    subject = Path(project)
    ids = _ticket_ids(task_a, task_b)
    if not ids:
        return []
    findings: list[str] = []
    handoffs = subject / ".recurspec" / "handoffs"
    evidence = subject / ".recurspec" / "evidence"
    trackers = _tracked_markdown(subject)
    for ticket_id in ids:
        handoff = handoffs / f"strategy-{ticket_id}.md"
        if handoff.is_file():
            findings.append(f"{ticket_id}: existing strategy handoff at {handoff}")
        if evidence.is_dir():
            for log in sorted(evidence.rglob("*.jsonl")):
                try:
                    if ticket_id in log.read_text(encoding="utf-8"):
                        findings.append(f"{ticket_id}: referenced in evidence log {log}")
                        break
                except (OSError, UnicodeError):
                    continue
        for tracker in trackers:
            try:
                text = tracker.read_text(encoding="utf-8")
            except (OSError, UnicodeError):
                continue
            if ticket_id in text:
                findings.append(f"{ticket_id}: already referenced in {tracker}")
    return findings


def init_pair(
    repository: str | Path,
    *,
    pair_id: str,
    project: str,
    task_a: str,
    task_b: str,
    hours: str,
    baseline: str,
    pair_dir: str = DEFAULT_PAIR_DIR,
) -> Path:
    repo = Path(repository).resolve()
    subject = Path(project).resolve()
    if is_recurspec_repository(subject):
        raise StudyInstrumentError(
            "Recurspec's own repository is excluded from the task population"
        )
    if not pair_id or "/" in pair_id or "\\" in pair_id or ".." in pair_id:
        raise StudyInstrumentError(f"unsafe pair id: {pair_id!r}")
    _reject_table_unsafe("task_a", task_a)
    _reject_table_unsafe("task_b", task_b)
    _reject_table_unsafe("hours", hours)
    findings = check_contamination(subject, task_a, task_b)
    if findings:
        raise StudyInstrumentError(
            "subject project already has Recurspec artifacts for one of these "
            "tasks -- the baseline/Recurspec-arm comparison would be contaminated "
            "before either arm starts: " + "; ".join(findings)
        )
    destination = (repo / pair_dir / f"{pair_id}.md").resolve()
    if repo not in destination.parents:
        raise StudyInstrumentError("pair path escapes the repository")
    if destination.exists():
        raise StudyInstrumentError(f"pair log already exists: {destination}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        _render_log(
            pair_id=pair_id,
            project=str(subject).replace("\\", "/"),
            task_a=task_a.strip(),
            task_b=task_b.strip(),
            hours=hours.strip(),
            baseline=baseline.strip(),
        ),
        encoding="utf-8",
    )
    return destination


def _parse_pending_tasks(text: str) -> tuple[str, str]:
    rows = re.findall(
        r"^\| Pending-[AB] \| ([^|]+) \|",
        text,
        flags=re.MULTILINE,
    )
    if len(rows) != 2:
        raise StudyInstrumentError("pair log does not have two unassigned pending tasks")
    return rows[0].strip(), rows[1].strip()


def assign_pair(path: str | Path) -> str:
    log = Path(path)
    try:
        text = log.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise StudyInstrumentError(f"could not read pair log: {exc}") from exc
    match = ASSIGNED_RE.search(text)
    if match is None:
        raise StudyInstrumentError("pair log is missing the assignment field")
    current = match.group(1).strip()
    if current and current != UNASSIGNED:
        raise StudyInstrumentError("pair is already assigned; refusing to re-flip")
    task_a, task_b = _parse_pending_tasks(text)
    recurspec_task = task_a if secrets.randbelow(2) == 0 else task_b
    baseline_task = task_b if recurspec_task == task_a else task_a
    result = (
        f"coin flip via secrets.randbelow(2); "
        f"Recurspec arm = {recurspec_task}; Baseline arm = {baseline_task}"
    )
    text = ASSIGNED_RE.sub(
        f"- Assignment method (coin flip / first-picked) and result: {result}",
        text,
        count=1,
    )
    hours_match = re.search(
        r"A-priori time estimate for each task \(set before either starts\): (.+)$",
        text,
        flags=re.MULTILINE,
    )
    hours = hours_match.group(1).strip() if hours_match else "unknown"
    text = re.sub(
        r"^\| Pending-A \| [^|]+ \| [^|]+ \| unassigned \|$",
        f"| Recurspec | {recurspec_task} | {hours} | "
        "Contract Tree + Decision Class + Evaluation Gate |",
        text,
        count=1,
        flags=re.MULTILINE,
    )
    text = re.sub(
        r"^\| Pending-B \| [^|]+ \| [^|]+ \| unassigned \|$",
        f"| Baseline | {baseline_task} | {hours} | "
        "Project's existing workflow, described as it is |",
        text,
        count=1,
        flags=re.MULTILINE,
    )
    log.write_text(text, encoding="utf-8")
    return result


def list_pairs(repository: str | Path, *, pair_dir: str = DEFAULT_PAIR_DIR) -> list[StudyPair]:
    root = Path(repository) / pair_dir
    if not root.is_dir():
        return []
    pairs: list[StudyPair] = []
    for path in sorted(root.glob("*.md")):
        if path.name.lower() == "readme.md":
            continue
        text = path.read_text(encoding="utf-8")
        pair_id = path.stem
        project_match = re.search(
            r"^- Project \(not recurspec itself\): `([^`]+)`",
            text,
            flags=re.MULTILINE,
        )
        assigned_match = ASSIGNED_RE.search(text)
        assignment = assigned_match.group(1).strip() if assigned_match else ""
        pairs.append(
            StudyPair(
                pair_id=pair_id,
                path=path.as_posix(),
                project=project_match.group(1) if project_match else "unknown",
                assigned=bool(assignment) and assignment != UNASSIGNED,
                assignment=assignment,
            )
        )
    return pairs


def _output_tail(completed: subprocess.CompletedProcess[str]) -> str:
    blob = ((completed.stdout or "") + (completed.stderr or "")).replace("\r\n", "\n")
    blob = blob.strip()
    if len(blob) > OUTPUT_TAIL_CHARS:
        blob = blob[-OUTPUT_TAIL_CHARS:]
    return blob.replace("```", "'''")


def _format_accept_record(result: AcceptResult) -> str:
    label = _ARM_LABEL[result.arm]
    tail = result.output_tail or "(empty)"
    tail_lines = "\n".join(f"    {line}" for line in tail.splitlines()) or "    (empty)"
    return (
        f"- Accepted {label}: {result.timestamp}\n"
        f"  - checker: {result.checker}\n"
        f"  - maker: {result.maker}\n"
        f"  - verify: `{result.verify_command}`\n"
        f"  - exit: {result.exit_code}\n"
        f"  - output tail:\n{tail_lines}"
    )


def _append_arm_start_record(text: str, *, arm: str, timestamp: str, record: str) -> str:
    label = _ARM_LABEL[arm]
    text = _ACCEPTED_NO_RE.sub(
        f"- Accepted implementation: yes ({label}, {timestamp})",
        text,
        count=1,
    )
    match = _ARM_START_SECTION.search(text)
    if match:
        body = match.group("body").rstrip() + "\n" + record + "\n"
        return text[: match.start()] + match.group("heading") + body + text[match.end() :]
    section = f"## Arm start (observed, not a-priori)\n\n{record}\n"
    marker = "## Post-hoc metrics"
    idx = text.find(marker)
    if idx != -1:
        return text[:idx] + section + "\n" + text[idx:]
    return text.rstrip() + "\n\n" + section


def accept_arm(
    path: str | Path,
    *,
    arm: str,
    checker: str,
    maker: str,
    verify_command: str,
    cwd: str | Path | None = None,
) -> AcceptResult:
    if arm not in _ARM_LABEL:
        raise StudyInstrumentError(
            f"arm must be one of {', '.join(sorted(_ARM_LABEL))}"
        )
    checker = checker.strip()
    maker = maker.strip()
    if not checker or not maker:
        raise StudyInstrumentError("checker and maker identities are required")
    if checker == maker:
        raise StudyInstrumentError("maker and checker must differ; refusing self-accept")
    if not verify_command or not str(verify_command).strip():
        raise StudyInstrumentError("verify command is required")

    log = Path(path)
    try:
        text = log.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise StudyInstrumentError(f"could not read pair log: {exc}") from exc
    assigned_match = ASSIGNED_RE.search(text)
    if assigned_match is None:
        raise StudyInstrumentError("pair log is missing the assignment field")
    current = assigned_match.group(1).strip()
    if not current or current == UNASSIGNED:
        raise StudyInstrumentError(
            "pair is unassigned; refuse to accept before a coin flip"
        )

    workdir = Path(cwd) if cwd is not None else Path.cwd()
    if not workdir.is_dir():
        raise StudyInstrumentError(f"verify cwd is not a directory: {workdir}")

    try:
        # verify_command is an operator-typed CLI argument (`recurspec study accept
        # --verify`), never Candidate- or network-controlled; shell=True is required to
        # support compound verify commands (e.g. "pytest -q && ruff check").
        completed = subprocess.run(  # noqa: S602
            verify_command,
            cwd=str(workdir),
            capture_output=True,
            text=True,
            shell=True,
            timeout=VERIFY_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired as exc:
        raise StudyInstrumentError(
            f"verify command timed out after {VERIFY_TIMEOUT_SECONDS}s"
        ) from exc
    except OSError as exc:
        raise StudyInstrumentError(f"could not run verify command: {exc}") from exc

    tail = _output_tail(completed)
    if completed.returncode != 0:
        detail = f": {tail}" if tail else ""
        raise StudyInstrumentError(
            f"verify command failed (exit {completed.returncode}); pair log not updated{detail}"
        )

    timestamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    result = AcceptResult(
        arm=arm,
        checker=checker,
        maker=maker,
        verify_command=verify_command,
        exit_code=completed.returncode,
        timestamp=timestamp,
        output_tail=tail,
    )
    log.write_text(
        _append_arm_start_record(
            text,
            arm=arm,
            timestamp=timestamp,
            record=_format_accept_record(result),
        ),
        encoding="utf-8",
    )
    return result
