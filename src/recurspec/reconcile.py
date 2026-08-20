"""Draft-only reconciliation of deterministic structural feedback."""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any

from .structure_gate import StructureDiagnostic, check_structure, infer_source_root

_RESPONSIBILITIES = re.compile(r"^\s*-\s+\*\*Responsibilities:\*\*\s*(.+)$", re.MULTILINE)


class ReconciliationInstrumentError(RuntimeError):
    """Structural evidence was incomplete or contradictory, so no draft is safe."""


@dataclass(frozen=True, order=True)
class ReconciliationAction:
    kind: str
    source_path: str
    contract_path: str | None
    reason: str
    draft_content: str | None = None

    def as_dict(self) -> dict[str, str | None]:
        return {
            "contract_path": self.contract_path,
            "draft_content": self.draft_content,
            "kind": self.kind,
            "reason": self.reason,
            "source_path": self.source_path,
        }


@dataclass(frozen=True)
class ReconciliationPlan:
    actions: tuple[ReconciliationAction, ...]
    deferred_empirical_events: int

    def as_dict(self) -> dict[str, Any]:
        return {
            "actions": [action.as_dict() for action in self.actions],
            "deferred_empirical_events": self.deferred_empirical_events,
        }


def _kebab(value: str) -> str:
    words = re.sub(r"(?<!^)(?=[A-Z])", "-", value).replace("_", "-")
    return re.sub(r"[^a-zA-Z0-9]+", "-", words).strip("-").lower()


def _draft_target(source_path: str, source_root: str, contract_root: str) -> str:
    relative = PurePosixPath(source_path).relative_to(PurePosixPath(source_root))
    parts = [_kebab(part) for part in relative.with_suffix("").parts]
    return PurePosixPath(contract_root, "drafts", *parts, "SYSTEM.md").as_posix()


def _draft_leaf(source_path: str) -> str:
    title = _kebab(PurePosixPath(source_path).stem).replace("-", " ").title()
    return f"""# {title} Draft (L1)

<!-- recurspec-contract: 1.0 -->

## 1. System Intent & Responsibility

Draft structural ownership for `{source_path}`; product behavior is deliberately unspecified
until Architect review.

## 2. Sub-System Decomposition

Atomic leaf (draft).

## 3. Interface Contracts

- **Inputs:** Unknown pending Architect review.
- **Outputs:** Unknown pending Architect review.

## 4. Invariants (EARS + Epistemic Stage)

- **[Ubiquitous]** THE SYSTEM SHALL NOT treat this structural draft as reviewed product behavior.
  - `EvidenceStage:` Unknown

## 5. Architectural Decisions (ADRs)

- **ADR-001:** Created only because deterministic structure analysis found unowned source.

## 6. Leaf Execution & Test Seam

- **Implementation:** `{source_path}`.
- **Tests:** Unknown pending Architect review.

## 7. Measurement Seams

- **Primary metric:** `architect_draft_acceptance_rate` (not yet measured).

## 8. Technology Resolution

Unresolved in this unapplied proposal. Architect review must either reject the draft or
assign its decision class through the normal Contract Tree and ROADMAP workflow.
"""


def _actions_for_drift(
    diagnostics: tuple[StructureDiagnostic, ...], source_root: str, contract_root: str
) -> list[ReconciliationAction]:
    actions: list[ReconciliationAction] = []
    uncontracted_sources = sorted(
        {
            item.path
            for item in diagnostics
            if item.code in {"structure.public.uncontracted", "structure.source.uncontracted"}
        }
    )
    for source_path in uncontracted_sources:
        actions.append(
            ReconciliationAction(
                "draft_leaf",
                source_path,
                _draft_target(source_path, source_root, contract_root),
                "source has no parent Contract Node",
                _draft_leaf(source_path),
            )
        )

    for item in diagnostics:
        if item.code == "structure.test.uncontracted":
            actions.append(
                ReconciliationAction(
                    "test_seam_review",
                    item.path,
                    None,
                    "test surface is not declared by a Contract Node",
                )
            )
        elif item.code in {
            "structure.implementation.ambiguous",
            "structure.implementation.missing",
            "structure.test_surface.missing",
        }:
            actions.append(
                ReconciliationAction(
                    "contract_repair_review", item.path, None, item.message
                )
            )
    return actions


def plan_reconciliation(
    repository: str | Path,
    *,
    source_root: str | None = None,
    contract_root: str = "docs/architecture",
    test_root: str = "tests",
    changed_files: set[str] | None = None,
    evidence_events: Sequence[Mapping[str, Any]] = (),
    bloat_line_limit: int = 150,
) -> ReconciliationPlan:
    """Return deterministic draft actions without changing repository files."""
    if bloat_line_limit < 1:
        raise ValueError("bloat_line_limit must be positive")
    if source_root is None:
        source_root = infer_source_root(repository) or "src"
    root = Path(repository).resolve()
    structure = check_structure(
        root,
        source_root=source_root,
        contract_root=contract_root,
        test_root=test_root,
        changed_files=changed_files,
    )
    if structure.instrument_error:
        raise ReconciliationInstrumentError(
            "structure instrument failed; refusing to generate reconciliation drafts"
        )

    actions = _actions_for_drift(structure.diagnostics, source_root, contract_root)
    contracts = root / contract_root
    for contract in sorted(contracts.rglob("SYSTEM.md")):
        text = contract.read_text(encoding="utf-8")
        line_count = len(text.splitlines())
        match = _RESPONSIBILITIES.search(text)
        responsibility_count = (
            len([item for item in match.group(1).split(";") if item.strip()]) if match else 0
        )
        if line_count > bloat_line_limit or responsibility_count > 3:
            relative = contract.relative_to(root).as_posix()
            reason = (
                f"Contract Node has {line_count} lines; limit is {bloat_line_limit}"
                if line_count > bloat_line_limit
                else f"Contract Node declares {responsibility_count} separable responsibilities"
            )
            actions.append(
                ReconciliationAction(
                    "split_review",
                    relative,
                    relative,
                    reason,
                )
            )

    deferred = sum(event.get("event_type") == "signal_d" for event in evidence_events)
    return ReconciliationPlan(tuple(sorted(set(actions))), deferred)
