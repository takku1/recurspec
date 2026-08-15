"""Split a work list into one strategy handoff per independently failing item."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any

LIST_ITEM_RE = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+(\S.*)$", re.MULTILINE)
TICKET_RE = re.compile(r"^[A-Za-z][A-Za-z0-9-]{0,31}$")
_DRIVE_LETTER_RE = re.compile(r"^[A-Za-z]:")


class FanoutInstrumentError(RuntimeError):
    """The fan-out command could not build a work list."""


@dataclass(frozen=True)
class FanoutItem:
    ticket_id: str
    goal: str
    handoff_path: str

    def as_dict(self) -> dict[str, str]:
        return {
            "goal": self.goal,
            "handoff": self.handoff_path,
            "ticket_id": self.ticket_id,
        }


@dataclass(frozen=True)
class FanoutPlan:
    items: tuple[FanoutItem, ...]
    rule: str = (
        "one handoff per item; run FRAME/RESEARCH/RESOLVE on that item only; "
        "do not keep siblings in the implementor packet"
    )

    def as_dict(self) -> dict[str, Any]:
        return {
            "items": [item.as_dict() for item in self.items],
            "rule": self.rule,
        }


def expand_items(raw_items: list[str]) -> list[str]:
    """Turn raw strings into goals. A single string that is itself a list splits."""
    expanded: list[str] = []
    for raw in raw_items:
        text = raw.strip()
        if not text:
            continue
        found = [match.strip() for match in LIST_ITEM_RE.findall(text)]
        if len(found) >= 2:
            expanded.extend(found)
        else:
            expanded.append(" ".join(text.split()))
    return expanded


def _handoff_markdown(ticket_id: str, goal: str) -> str:
    return (
        f"# Strategy Handoff — {ticket_id}\n\n"
        "## Target\n\n"
        "- Contract: (fill after FRAME)\n"
        f"- Ticket: `{ticket_id}`\n\n"
        "## Goal\n\n"
        f"{goal}\n\n"
        "## Non-goals\n\n"
        "Sibling items from this fan-out are out of scope for this handoff.\n\n"
        "## Context rule\n\n"
        "Load only this handoff and the target contract. Do not keep sibling items "
        "in this packet.\n\n"
        "## Required invariants\n\n"
        "(fill during FRAME)\n\n"
        "## Test and observation seams\n\n"
        "(fill during SPECIFY)\n\n"
        "## KEEP gate\n\n"
        "Human review required if no independent checker is available.\n"
    )


def _contained_output_dir(output_dir: str | Path) -> str:
    raw = str(output_dir).replace("\\", "/")
    if not raw or raw.startswith("/") or _DRIVE_LETTER_RE.match(raw):
        raise FanoutInstrumentError(
            f"output directory {output_dir!r} must be repository-relative"
        )
    posix = PurePosixPath(raw)
    if ".." in posix.parts:
        raise FanoutInstrumentError(
            f"output directory {output_dir!r} escapes the repository"
        )
    return posix.as_posix()


def plan_fanout(
    raw_items: list[str],
    *,
    prefix: str = "FAN",
    output_dir: str | Path = ".recurspec/handoffs",
) -> FanoutPlan:
    if not TICKET_RE.match(prefix):
        raise FanoutInstrumentError(
            f"prefix {prefix!r} must be a short ticket stem (letters, digits, hyphen)"
        )
    destination = _contained_output_dir(output_dir)
    goals = expand_items(raw_items)
    if len(goals) < 2:
        raise FanoutInstrumentError(
            "a work list must expand to at least two items; "
            "design a single item fully instead of inventing siblings"
        )
    width = max(2, len(str(len(goals))))
    items: list[FanoutItem] = []
    for index, goal in enumerate(goals, start=1):
        ticket_id = f"{prefix}-{index:0{width}d}"
        relative = f"{destination}/strategy-{ticket_id}.md"
        items.append(FanoutItem(ticket_id=ticket_id, goal=goal, handoff_path=relative))
    return FanoutPlan(tuple(items))


def write_fanout(plan: FanoutPlan, *, repository: str | Path = ".") -> list[Path]:
    root = Path(repository).resolve()
    if not root.is_dir():
        raise FanoutInstrumentError(f"repository does not exist: {repository}")
    written: list[Path] = []
    for item in plan.items:
        relative = _contained_output_dir(item.handoff_path)
        path = (root / relative).resolve()
        if path != root and root not in path.parents:
            raise FanoutInstrumentError(
                f"handoff path {item.handoff_path!r} escapes the repository"
            )
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(_handoff_markdown(item.ticket_id, item.goal), encoding="utf-8")
        written.append(path)
    return written


def render_fanout(plan: FanoutPlan) -> str:
    lines = [f"items: {len(plan.items)}", f"rule: {plan.rule}"]
    lines.extend(
        f"{item.ticket_id}\t{item.handoff_path}\t{item.goal}" for item in plan.items
    )
    return "\n".join(lines) + "\n"
