"""One read-only inspection seam over Recurspec's deterministic checkers."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .contract import ContractInstrumentError, audit_evidence_stages, validate_contract
from .frontier import check_frontiers
from .structure_gate import available_adapters, check_structure
from .technology_resolver import ResolutionInstrumentError, audit_resolutions

Detail = str | int | float | bool | None
CHECKERS = ("contract", "evidence", "structure", "resolution", "frontier")


@dataclass(frozen=True, order=True)
class Finding:
    checker: str
    code: str
    evidence_stage: str
    evidence_class: str
    message: str
    details: tuple[tuple[str, Detail], ...] = ()
    blocking: bool = True

    @property
    def subject(self) -> str:
        """Where the finding is, for human output.

        The JSON envelope always carried the locating details; text output printed only
        checker/code/message, which rendered every ``Unknown`` evidence finding as the
        same unactionable line (R-701).
        """
        details = dict(self.details)
        path = details.get("path")
        if path is None:
            return self.checker
        index = details.get("invariant_index")
        return f"{path}:{index}" if index is not None else str(path)

    def as_dict(self) -> dict[str, Any]:
        return {
            "blocking": self.blocking,
            "checker": self.checker,
            "code": self.code,
            "details": dict(self.details),
            "evidence_class": self.evidence_class,
            "evidence_stage": self.evidence_stage,
            "message": self.message,
        }


@dataclass(frozen=True)
class CheckReport:
    checks: tuple[str, ...]
    findings: tuple[Finding, ...]
    indeterminate: bool = False

    @property
    def valid(self) -> bool:
        return not self.indeterminate and not any(item.blocking for item in self.findings)

    @property
    def exit_code(self) -> int:
        if self.indeterminate:
            return 2
        return int(not self.valid)

    def as_dict(self) -> dict[str, Any]:
        return {
            "checks": list(self.checks),
            "findings": [item.as_dict() for item in self.findings],
            "indeterminate": self.indeterminate,
            "valid": self.valid,
        }


def _relative(repository: Path, path: str) -> str:
    candidate = Path(path)
    if not candidate.is_absolute():
        return candidate.as_posix()
    try:
        return candidate.resolve().relative_to(repository).as_posix()
    except ValueError:
        return candidate.as_posix()


def check_project(
    repository: str | Path,
    *,
    checks: tuple[str, ...] | None = None,
    changed_files: set[str] | None = None,
) -> CheckReport:
    """Run selected deterministic checks without changing repository state."""
    root = Path(repository).resolve()
    requested = set(checks or CHECKERS)
    unknown = requested - set(CHECKERS)
    if unknown:
        raise ValueError("unknown checker(s): " + ", ".join(sorted(unknown)))
    selected = tuple(checker for checker in CHECKERS if checker in requested)
    if not root.is_dir():
        return CheckReport(
            selected,
            (
                Finding(
                    "inspection",
                    "inspection.repository.missing",
                    "Unknown",
                    "static_structure",
                    "repository does not exist",
                    (("path", root.as_posix()),),
                ),
            ),
            indeterminate=True,
        )
    findings: list[Finding] = []
    indeterminate = False

    if "contract" in selected:
        try:
            result = validate_contract(root / "docs" / "architecture")
        except ContractInstrumentError as exc:
            findings.append(
                Finding(
                    "contract",
                    "contract.instrument_error",
                    "Unknown",
                    "static_structure",
                    str(exc),
                )
            )
            indeterminate = True
        else:
            findings.extend(
                Finding(
                    "contract",
                    item.rule_code,
                    "Observed",
                    "static_structure",
                    item.message,
                    (("path", _relative(root, item.path)),),
                )
                for item in result.diagnostics
            )

    if "evidence" in selected:
        try:
            audit = audit_evidence_stages(root / "docs" / "architecture")
        except ContractInstrumentError as exc:
            findings.append(
                Finding(
                    "evidence",
                    "evidence.instrument_error",
                    "Unknown",
                    "static_structure",
                    str(exc),
                )
            )
            indeterminate = True
        else:
            for item in (*audit.unlicensed, *audit.unknowns):
                code = (
                    "evidence.stage.unknown"
                    if item.stage == "Unknown"
                    else "evidence.claim.unlicensed"
                )
                findings.append(
                    Finding(
                        "evidence",
                        code,
                        item.stage,
                        "static_structure",
                        item.issue,
                        (
                            ("invariant_index", item.invariant_index),
                            ("path", _relative(root, item.path)),
                        ),
                        blocking=False,
                    )
                )

    if "structure" in selected:
        try:
            result = check_structure(
                root,
                changed_files=changed_files,
                adapters=available_adapters(),
            )
        except (OSError, ValueError) as exc:
            findings.append(
                Finding(
                    "structure",
                    "structure.instrument_error",
                    "Unknown",
                    "static_structure",
                    str(exc),
                )
            )
            indeterminate = True
        else:
            indeterminate = indeterminate or result.instrument_error
            findings.extend(
                Finding(
                    "structure",
                    item.code,
                    "Unknown" if result.instrument_error else "Observed",
                    "static_structure",
                    item.message,
                    tuple(
                        detail
                        for detail in (
                            ("path", item.path),
                            ("symbol", item.symbol),
                        )
                        if detail[1] is not None
                    ),
                )
                for item in result.diagnostics
            )

    if "resolution" in selected:
        try:
            result = audit_resolutions(root)
        except (OSError, ValueError, ResolutionInstrumentError) as exc:
            findings.append(
                Finding(
                    "resolution",
                    "resolution.instrument_error",
                    "Unknown",
                    "static_structure",
                    str(exc),
                )
            )
            indeterminate = True
        else:
            indeterminate = indeterminate or result.indeterminate
            findings.extend(
                Finding(
                    "resolution",
                    item.code,
                    "Unknown" if item.code == "resolution.inventory.unavailable" else "Observed",
                    "static_structure",
                    item.message,
                    (("path", item.path),),
                )
                for item in result.diagnostics
            )

    if "frontier" in selected:
        try:
            result = check_frontiers(root / ".recurspec" / "frontiers", root)
        except (OSError, UnicodeError) as exc:
            findings.append(
                Finding(
                    "frontier",
                    "frontier.instrument_error",
                    "Unknown",
                    "static_structure",
                    str(exc),
                )
            )
            indeterminate = True
        else:
            findings.extend(
                Finding(
                    "frontier",
                    "frontier.contract.missing",
                    "Observed",
                    "static_structure",
                    "Research Frontier ticket does not point to an existing Contract Node",
                    (("ticket", ticket),),
                )
                for ticket in result.broken
            )

    return CheckReport(tuple(selected), tuple(sorted(findings)), indeterminate)
