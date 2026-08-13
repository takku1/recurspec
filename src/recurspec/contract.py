"""Versioned Markdown Contract Node validation."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from importlib.resources import files
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

VERSION_RE = re.compile(r"<!--\s*recurspec-contract:\s*([^\s]+)\s*-->")
TITLE_RE = re.compile(r"^#\s+(.+?)\s+\(L(\d+)\)\s*$", re.MULTILINE)
SECTION_RE = re.compile(r"^##\s+([1-8])\.\s+.+$", re.MULTILINE)
INVARIANT_RE = re.compile(r"^-\s+\*\*\[([^]]+)]\*\*\s+(.+)$")
EVIDENCE_RE = re.compile(r"^\s+-\s+`EvidenceStage:`\s*(\S+)\s*$")
INTERFACE_RE = re.compile(r"^\s*-\s+\*\*(Inputs|Outputs):\*\*\s*(.*)$", re.MULTILINE)
PORT_RE = re.compile(r"`([^`]+)`")
LINK_RE = re.compile(r"\[[^]]+]\(([^)]+)\)")

EVIDENCE_STAGES = {
    "Unknown",
    "Observed",
    "Sampled",
    "Inferred",
    "Measured",
    "Proved",
    "Refuted",
}
EARS_PATTERNS = {
    "Ubiquitous": re.compile(r"\bSHALL\b", re.IGNORECASE),
    "Conditional": re.compile(r"^IF\b.+\bTHEN\b.+\bSHALL\b", re.IGNORECASE),
    "Event-driven": re.compile(r"^WHEN\b.+\bSHALL\b", re.IGNORECASE),
    "State-driven": re.compile(r"^WHILE\b.+\bSHALL\b", re.IGNORECASE),
}


class ContractInstrumentError(RuntimeError):
    """The validation instrument could not inspect the requested contract."""


@dataclass(frozen=True, order=True)
class Diagnostic:
    path: str
    rule_code: str
    message: str

    def as_dict(self) -> dict[str, str]:
        return {"path": self.path, "rule_code": self.rule_code, "message": self.message}


@dataclass(frozen=True)
class ValidationResult:
    contracts: tuple[dict[str, Any], ...]
    diagnostics: tuple[Diagnostic, ...]

    @property
    def valid(self) -> bool:
        return not self.diagnostics


def _schema() -> dict[str, Any]:
    resource = files("recurspec").joinpath("schemas/contract-node-1.0.schema.json")
    try:
        schema = json.loads(resource.read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)
        return schema
    except Exception as exc:
        raise ContractInstrumentError(
            f"bundled contract schema could not be loaded: {exc}"
        ) from exc


def _sections(text: str) -> dict[str, str]:
    matches = list(SECTION_RE.finditer(text))
    return {
        match.group(1): text[
            match.end() : matches[index + 1].start() if index + 1 < len(matches) else None
        ].strip()
        for index, match in enumerate(matches)
    }


def _invariants(section: str) -> tuple[list[dict[str, str]], list[tuple[str, str]]]:
    normalized: list[dict[str, str]] = []
    problems: list[tuple[str, str]] = []
    lines = section.splitlines()
    starts = [
        (index, match)
        for index, line in enumerate(lines)
        if (match := INVARIANT_RE.match(line))
    ]
    for position, (index, match) in enumerate(starts):
        pattern, first_statement_line = match.groups()
        next_index = starts[position + 1][0] if position + 1 < len(starts) else len(lines)
        evidence = None
        statement_lines = [first_statement_line]
        for continuation in lines[index + 1 : next_index]:
            if evidence_match := EVIDENCE_RE.match(continuation):
                evidence = evidence_match
                break
            if continuation.strip():
                statement_lines.append(continuation.strip())
        statement = " ".join(statement_lines)
        if pattern not in EARS_PATTERNS or not EARS_PATTERNS.get(pattern, re.compile(r"a^")).search(
            statement
        ):
            problems.append(
                (
                    "contract.invariant.ears",
                    f"invariant {index + 1} does not match a recognized EARS pattern",
                )
            )
        if evidence is None or evidence.group(1) not in EVIDENCE_STAGES:
            problems.append(
                (
                    "contract.invariant.evidence-stage",
                    f"invariant {index + 1} lacks a recognized Evidence Stage",
                )
            )
        if (
            pattern in EARS_PATTERNS
            and evidence is not None
            and evidence.group(1) in EVIDENCE_STAGES
        ):
            normalized.append(
                {
                    "ears_pattern": pattern,
                    "statement": statement,
                    "evidence_stage": evidence.group(1),
                }
            )
    return normalized, problems


def _normalize(path: Path) -> tuple[dict[str, Any] | None, list[Diagnostic]]:
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise ContractInstrumentError(f"could not read {path}: {exc}") from exc

    display_path = path.as_posix()
    diagnostics: list[Diagnostic] = []
    version = VERSION_RE.search(text)
    if version is None:
        diagnostics.append(
            Diagnostic(
                display_path,
                "contract.version.missing",
                "missing '<!-- recurspec-contract: 1.0 -->' metadata",
            )
        )
        return None, diagnostics
    if version.group(1) != "1.0":
        diagnostics.append(
            Diagnostic(
                display_path,
                "contract.version.unsupported",
                f"unsupported contract version {version.group(1)!r}; expected '1.0'",
            )
        )
        return None, diagnostics

    title = TITLE_RE.search(text)
    if title is None:
        diagnostics.append(
            Diagnostic(
                display_path, "contract.title.invalid", "expected '# TITLE (L<level>)' heading"
            )
        )
        return None, diagnostics

    sections = _sections(text)
    required_sections = ("1", "2", "3", "4", "5")
    if sections.get("2", "").strip().lower().startswith("atomic leaf."):
        required_sections += ("6", "7", "8")
    for number in required_sections:
        if number not in sections:
            diagnostics.append(
                Diagnostic(
                    display_path,
                    "contract.heading.missing",
                    f"required section {number} heading is missing",
                )
            )
    invariants, problems = _invariants(sections.get("4", ""))
    diagnostics.extend(Diagnostic(display_path, code, message) for code, message in problems)
    atomic_leaf = sections.get("2", "").strip().lower().startswith("atomic leaf.")
    interface_lines = {
        name.lower(): PORT_RE.findall(value)
        for name, value in INTERFACE_RE.findall(sections.get("3", ""))
    }
    children = [] if atomic_leaf else LINK_RE.findall(sections.get("2", ""))
    contract: dict[str, Any] = {
        "contract_version": "1.0",
        "title": title.group(1),
        "level": int(title.group(2)),
        "atomic_leaf": atomic_leaf,
        "inputs": interface_lines.get("inputs", []),
        "outputs": interface_lines.get("outputs", []),
        "children": children,
        "sections": sections,
        "invariants": invariants,
    }
    for error in Draft202012Validator(_schema()).iter_errors(contract):
        if error.validator == "required" and list(error.absolute_path) == ["sections"]:
            continue
        if problems and list(error.absolute_path) == ["invariants"]:
            continue
        location = "/".join(str(part) for part in error.absolute_path) or "$"
        diagnostics.append(
            Diagnostic(display_path, "contract.schema", f"{location}: {error.message}")
        )
    return contract, diagnostics


def validate_contract(path: str | Path) -> ValidationResult:
    """Validate one SYSTEM.md or every recursively discovered SYSTEM.md in a directory."""
    requested = Path(path)
    if requested.is_dir():
        paths = sorted(requested.rglob("SYSTEM.md"), key=lambda item: item.as_posix())
        if not paths:
            return ValidationResult(
                (),
                (
                    Diagnostic(
                        requested.as_posix(),
                        "contract.discovery.empty",
                        "directory contains no recursively discovered SYSTEM.md files",
                    ),
                ),
            )
    elif requested.is_file():
        paths = [requested]
    else:
        raise ContractInstrumentError(f"contract path does not exist: {requested}")

    contracts: list[dict[str, Any]] = []
    diagnostics: list[Diagnostic] = []
    normalized_by_path: dict[Path, dict[str, Any]] = {}
    for contract_path in paths:
        contract, contract_diagnostics = _normalize(contract_path)
        if contract is not None:
            contracts.append(contract)
            normalized_by_path[contract_path.resolve()] = contract
        diagnostics.extend(contract_diagnostics)
    if requested.is_dir():
        tree_root = requested.resolve()
        for parent_path, parent in normalized_by_path.items():
            if parent["atomic_leaf"]:
                continue
            available = set(parent["inputs"])
            remaining = []
            seen_children: set[Path] = set()
            for child_link in parent["children"]:
                linked_path = Path(child_link)
                if linked_path.is_absolute():
                    diagnostics.append(
                        Diagnostic(
                            parent_path.as_posix(),
                            "contract.child.not-relative",
                            f"child link {child_link!r} must be relative",
                        )
                    )
                    continue
                child_path = (parent_path.parent / linked_path).resolve()
                if not child_path.is_relative_to(tree_root):
                    diagnostics.append(
                        Diagnostic(
                            parent_path.as_posix(),
                            "contract.child.outside-tree",
                            f"child link {child_link!r} resolves outside the checked tree",
                        )
                    )
                    continue
                if child_path.is_dir():
                    child_path = child_path / "SYSTEM.md"
                if child_path in seen_children:
                    diagnostics.append(
                        Diagnostic(
                            parent_path.as_posix(),
                            "contract.child.duplicate",
                            f"child link {child_link!r} resolves to a duplicate Contract Node",
                        )
                    )
                    continue
                seen_children.add(child_path)
                child = normalized_by_path.get(child_path)
                if child is None:
                    diagnostics.append(
                        Diagnostic(
                            parent_path.as_posix(),
                            "contract.child.missing",
                            f"child link {child_link!r} does not resolve to a Contract Node",
                        )
                    )
                    continue
                if child["level"] != parent["level"] + 1:
                    diagnostics.append(
                        Diagnostic(
                            child_path.as_posix(),
                            "contract.child.level",
                            f"child level {child['level']} must equal parent level "
                            f"{parent['level']} plus one",
                        )
                    )
                    continue
                remaining.append(child)
            while remaining:
                satisfiable = [child for child in remaining if set(child["inputs"]) <= available]
                if not satisfiable:
                    break
                for child in satisfiable:
                    available.update(child["outputs"])
                    remaining.remove(child)
            for child in remaining:
                child_path = next(
                    path for path, normalized in normalized_by_path.items() if normalized is child
                )
                for input_port in child["inputs"]:
                    if input_port not in available:
                        diagnostics.append(
                            Diagnostic(
                                child_path.as_posix(),
                                "contract.interface.input.unsatisfied",
                                f"child input {input_port!r} is unavailable during composition",
                            )
                        )
            for output in parent["outputs"]:
                if output not in available:
                    diagnostics.append(
                        Diagnostic(
                            parent_path.as_posix(),
                            "contract.interface.output.unsatisfied",
                            f"parent output {output!r} is unavailable after child composition",
                        )
                    )
    return ValidationResult(tuple(contracts), tuple(sorted(diagnostics)))
