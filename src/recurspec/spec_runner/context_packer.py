"""Context Packer: assemble the smallest packet a worker needs for one node's turn.

Implements docs/architecture/spec-runner/context-packer/SYSTEM.md. Operates on nodes
that already exist as a ``SYSTEM.md`` file (even a draft); framing a genuinely new node
that has no file yet is Runner-level orchestration (R-200), not this leaf's job.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from importlib.resources import files
from pathlib import Path
from typing import Any

from ..contract import ContractInstrumentError, build_tree_index

# Conservative token estimate: real English/code averages ~4 chars/token: dividing by a
# smaller number over-estimates, which is the safe direction (ADR-001: estimate high).
# This is an approximation, not a real tokenizer - callers must not treat it as exact.
CHARS_PER_TOKEN = 3


def estimate_tokens(text: str) -> int:
    return math.ceil(len(text) / CHARS_PER_TOKEN) if text else 0


def contract_card() -> str:
    """The packet's byte-identical leading prefix, generated from design.md, not
    maintained separately (ADR-003)."""
    resource = files("recurspec").joinpath("skill/references/design.md")
    return resource.read_text(encoding="utf-8")


@dataclass(frozen=True)
class Packet:
    contract_card: str
    parent_context: str
    sibling_interfaces: str
    own_draft: str
    survey_context: str
    estimated_tokens: int
    sections_included: tuple[str, ...]


@dataclass(frozen=True)
class BudgetOverflow:
    largest_contributor: str
    estimated_tokens: int
    max_tokens_per_node: int


@dataclass(frozen=True)
class SchemaRejected:
    diagnostics: tuple[str, ...]


def _section(sections: dict[str, str], number: str, heading: str) -> str:
    return f"## {number}. {heading}\n\n{sections.get(number, '')}"


def _parent_context(node: dict[str, Any]) -> str:
    """A parent contributes §1 (responsibility) and §3 (interfaces) - never more."""
    sections = node["sections"]
    return (
        _section(sections, "1", "System Intent & Responsibility")
        + "\n\n"
        + _section(sections, "3", "Interface Contracts")
    )


def _sibling_interface(node: dict[str, Any]) -> str:
    """A sibling contributes §3 only, never its body - packet size is then linear in
    sibling count, not sibling depth."""
    return _section(node["sections"], "3", "Interface Contracts")


def pack(
    node_id: str,
    tree_root: str | Path,
    max_tokens_per_node: int,
    survey_result: Any = None,
    phase: str = "frame",
) -> Packet | BudgetOverflow | SchemaRejected:
    """Assemble the bounded packet for one node's loop turn, or refuse.

    Never includes ancestors above the parent or any uncle subtree (invariant 1).
    Refuses with ``BudgetOverflow`` rather than truncate (invariant 3). The schema
    pre-check (invariant 4) is indexing the whole tree up front: an invalid Contract
    Tree anywhere refuses to pack rather than dispatch a worker against ground that
    cannot be trusted.
    """
    tree_root = Path(tree_root)
    try:
        index = build_tree_index(tree_root)
    except ContractInstrumentError as exc:
        return SchemaRejected(diagnostics=(str(exc),))

    if node_id not in index:
        raise KeyError(f"node_id {node_id!r} not found in the Contract Tree at {tree_root}")
    node = index[node_id]
    own_draft = node["path"].read_text(encoding="utf-8")

    parent_id = node["parent_id"]
    parent_context = _parent_context(index[parent_id]) if parent_id is not None else ""

    sibling_ids = sorted(
        other_id
        for other_id, other in index.items()
        if other["parent_id"] == parent_id and other_id != node_id
    )
    sibling_interfaces = "\n\n".join(_sibling_interface(index[sid]) for sid in sibling_ids)

    survey_context = "" if survey_result is None else str(survey_result)
    card = contract_card()

    parts = {
        "contract_card": card,
        "parent_context": parent_context,
        "sibling_interfaces": sibling_interfaces,
        "own_draft": own_draft,
        "survey_context": survey_context,
    }
    estimates = {name: estimate_tokens(text) for name, text in parts.items()}
    total = sum(estimates.values())
    if total > max_tokens_per_node:
        largest_contributor = max(estimates, key=lambda name: estimates[name])
        return BudgetOverflow(
            largest_contributor=largest_contributor,
            estimated_tokens=total,
            max_tokens_per_node=max_tokens_per_node,
        )

    return Packet(
        contract_card=card,
        parent_context=parent_context,
        sibling_interfaces=sibling_interfaces,
        own_draft=own_draft,
        survey_context=survey_context,
        estimated_tokens=total,
        sections_included=tuple(name for name, text in parts.items() if text),
    )
