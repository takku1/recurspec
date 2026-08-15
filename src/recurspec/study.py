"""Case-study pair apparatus for the pre-registered R-400–R-403 protocol."""

from __future__ import annotations

import re
import secrets
from dataclasses import dataclass
from pathlib import Path
from typing import Any

DEFAULT_PAIR_DIR = "docs/research/pairs"
PROTOCOL_DATE = "2026-08-14"
ASSIGNED_RE = re.compile(
    r"^- Assignment method \(coin flip / first-picked\) and result:\s*(.*?)\s*$",
    re.MULTILINE,
)
UNASSIGNED = "unassigned"


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


def is_recurspec_repository(path: str | Path) -> bool:
    pyproject = Path(path) / "pyproject.toml"
    if not pyproject.is_file():
        return False
    try:
        text = pyproject.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return False
    return bool(re.search(r'(?m)^name\s*=\s*"recurspec"\s*$', text))


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
        "## Post-hoc metrics\n\n"
        "List any number reported that is not in the protocol §5 table. "
        "Label each `post-hoc`.\n"
    )


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
