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
    "Optional": re.compile(r"^WHERE\b.+\bSHALL\b", re.IGNORECASE),
}

# Complex requirements combine two or more EARS keyword clauses in one statement
# (Mavin et al., e.g. "WHILE <state>, WHEN <trigger>, THE SYSTEM SHALL ..."). A
# statement only qualifies if it leads with a recognized keyword and actually
# combines at least two of the four keyword-anchored patterns below (Ubiquitous
# is excluded: bare SHALL is not a combinable keyword clause).
COMPLEX_LEAD_RE = re.compile(r"^(WHILE|WHEN|IF|WHERE)\b", re.IGNORECASE)
COMPLEX_KEYWORDS = {
    "State-driven": re.compile(r"\bWHILE\b", re.IGNORECASE),
    "Event-driven": re.compile(r"\bWHEN\b", re.IGNORECASE),
    "Conditional": re.compile(r"\bIF\b.+\bTHEN\b", re.IGNORECASE),
    "Optional": re.compile(r"\bWHERE\b", re.IGNORECASE),
}


def _matches_ears_pattern(pattern: str, statement: str) -> bool:
    if pattern == "Complex":
        if not COMPLEX_LEAD_RE.match(statement):
            return False
        keyword_hits = sum(1 for regex in COMPLEX_KEYWORDS.values() if regex.search(statement))
        return keyword_hits >= 2 and bool(re.search(r"\bSHALL\b", statement, re.IGNORECASE))
    return pattern in EARS_PATTERNS and bool(EARS_PATTERNS[pattern].search(statement))


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


ATOMIC_LEAF_RE = re.compile(r"^\*{0,2}atomic leaf\s*(\([^)]*\))?\s*\.", re.IGNORECASE)


def _is_atomic_leaf(section_two: str) -> bool:
    """Section 2 declares a leaf via "Atomic leaf.", optionally bold and/or annotated
    with a parenthetical stage or reason, e.g. "**Atomic leaf (procured).**"."""
    return bool(ATOMIC_LEAF_RE.match(section_two.strip()))


DECISION_CLASS_RE = re.compile(
    r"^\s*-\s*\*\*Decision class:\*\*\s*(BUY|ADOPT|WRAP|BUILD|DEFER)\s*$",
    re.IGNORECASE | re.MULTILINE,
)


def decision_class(sections: dict[str, str]) -> str | None:
    """Extract a terminal node's §8 Decision class (BUY/ADOPT/WRAP/BUILD/DEFER).

    Returns ``None`` for a non-terminal node or a §8 block this instrument
    cannot parse - callers must not guess a class from absence.
    """
    match = DECISION_CLASS_RE.search(sections.get("8", ""))
    return match.group(1).upper() if match else None


def resolve_child_path(parent_path: Path, child_link: str) -> Path:
    """Resolve a child link relative to its parent's directory, expanding a
    directory link to the ``SYSTEM.md`` it implies. Pure path resolution -
    does not check the result is in-tree or exists; ``validate_contract``
    owns those diagnostics.
    """
    child_path = (parent_path.parent / Path(child_link)).resolve()
    if child_path.is_dir():
        child_path = child_path / "SYSTEM.md"
    return child_path


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
        matches_ears = _matches_ears_pattern(pattern, statement)
        stage = evidence.group(1) if evidence is not None else None
        if not matches_ears:
            problems.append(
                (
                    "contract.invariant.ears",
                    f"invariant {index + 1} does not match a recognized EARS pattern",
                )
            )
        if stage not in EVIDENCE_STAGES:
            problems.append(
                (
                    "contract.invariant.evidence-stage",
                    f"invariant {index + 1} lacks a recognized Evidence Stage",
                )
            )
        elif matches_ears:
            normalized.append(
                {
                    "ears_pattern": pattern,
                    "statement": statement,
                    "evidence_stage": stage,
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
    atomic_leaf = _is_atomic_leaf(sections.get("2", ""))
    required_sections = ("1", "2", "3", "4", "5")
    if atomic_leaf:
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
    interface_lines = {
        name.lower(): PORT_RE.findall(value)
        for name, value in INTERFACE_RE.findall(sections.get("3", ""))
    }
    children = [] if atomic_leaf else LINK_RE.findall(sections.get("2", ""))
    if not atomic_leaf and not children:
        diagnostics.append(
            Diagnostic(
                display_path,
                "contract.node.hollow",
                "non-leaf Contract Node declares no children; add a child link in "
                "section 2 or mark it 'Atomic leaf.'",
            )
        )
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


CHECK_CITE_RE = re.compile(
    r"(?:`?test_[A-Za-z0-9_]+`?|`?(?:checks|measure)\.sh`?)"
)
LICENSED_STAGES = frozenset({"Sampled", "Measured", "Proved"})


@dataclass(frozen=True, order=True)
class EvidenceFinding:
    path: str
    invariant_index: int
    stage: str
    issue: str

    def as_dict(self) -> dict[str, str | int]:
        return {
            "invariant_index": self.invariant_index,
            "issue": self.issue,
            "path": self.path,
            "stage": self.stage,
        }


@dataclass(frozen=True)
class EvidenceAudit:
    counts: dict[str, int]
    unlicensed: tuple[EvidenceFinding, ...]
    unknowns: tuple[EvidenceFinding, ...]

    def as_dict(self) -> dict[str, Any]:
        return {
            "counts": dict(self.counts),
            "unlicensed": [item.as_dict() for item in self.unlicensed],
            "unknowns": [item.as_dict() for item in self.unknowns],
        }


def _empty_stage_counts() -> dict[str, int]:
    return dict.fromkeys(sorted(EVIDENCE_STAGES), 0)


def _contract_paths(path: str | Path) -> list[Path]:
    requested = Path(path)
    if requested.is_dir():
        return sorted(requested.rglob("SYSTEM.md"), key=lambda item: item.as_posix())
    if requested.is_file():
        return [requested]
    raise ContractInstrumentError(f"contract path does not exist: {requested}")


def audit_evidence_stages(path: str | Path) -> EvidenceAudit:
    """Count Evidence Stages and list claims that name no check.

    Observation only: this never adds diagnostics to ``validate_contract``.
    A Sampled/Measured/Proved invariant is unlicensed when its statement does
    not name ``test_*``, ``checks.sh``, or ``measure.sh``.
    """
    counts = _empty_stage_counts()
    unlicensed: list[EvidenceFinding] = []
    unknowns: list[EvidenceFinding] = []
    for contract_path in _contract_paths(path):
        contract, _diagnostics = _normalize(contract_path)
        if contract is None:
            continue
        display = contract_path.as_posix()
        for index, invariant in enumerate(contract.get("invariants") or [], start=1):
            stage = invariant["evidence_stage"]
            counts[stage] = counts.get(stage, 0) + 1
            if stage == "Unknown":
                unknowns.append(
                    EvidenceFinding(
                        path=display,
                        invariant_index=index,
                        stage=stage,
                        issue="Unknown",
                    )
                )
            elif stage in LICENSED_STAGES and not CHECK_CITE_RE.search(
                invariant["statement"]
            ):
                unlicensed.append(
                    EvidenceFinding(
                        path=display,
                        invariant_index=index,
                        stage=stage,
                        issue=f"{stage} names no check",
                    )
                )
    return EvidenceAudit(
        counts=counts,
        unlicensed=tuple(sorted(unlicensed)),
        unknowns=tuple(sorted(unknowns)),
    )


def validate_contract(path: str | Path) -> ValidationResult:
    """Validate one SYSTEM.md or every recursively discovered SYSTEM.md in a directory."""
    requested = Path(path)
    paths = _contract_paths(requested)
    if requested.is_dir() and not paths:
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
        referenced_by: dict[Path, list[Path]] = {}
        resolved_children: dict[Path, list[Path]] = {}
        for parent_path, parent in normalized_by_path.items():
            if parent["atomic_leaf"]:
                continue
            available = set(parent["inputs"])
            remaining: list[tuple[Path, dict[str, Any]]] = []
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
                child_path = resolve_child_path(parent_path, child_link)
                if not child_path.is_relative_to(tree_root):
                    diagnostics.append(
                        Diagnostic(
                            parent_path.as_posix(),
                            "contract.child.outside-tree",
                            f"child link {child_link!r} resolves outside the checked tree",
                        )
                    )
                    continue
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
                referenced_by.setdefault(child_path, []).append(parent_path)
                resolved_children.setdefault(parent_path, []).append(child_path)
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
                remaining.append((child_path, child))
            while remaining:
                satisfiable = {
                    path for path, child in remaining if set(child["inputs"]) <= available
                }
                if not satisfiable:
                    break
                for path, child in remaining:
                    if path in satisfiable:
                        available.update(child["outputs"])
                remaining = [item for item in remaining if item[0] not in satisfiable]
            for child_path, child in remaining:
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

        def _relative(node_path: Path) -> str:
            return node_path.relative_to(tree_root).as_posix()

        for child_path, parents in sorted(referenced_by.items()):
            if len(parents) > 1:
                diagnostics.append(
                    Diagnostic(
                        child_path.as_posix(),
                        "contract.child.multiple_parents",
                        "Contract Node is linked from more than one parent: "
                        + ", ".join(sorted(_relative(p) for p in parents)),
                    )
                )

        roots = sorted(
            (path for path in normalized_by_path if path not in referenced_by),
            key=lambda item: item.as_posix(),
        )
        if len(roots) != 1:
            root_names = ", ".join(_relative(p) for p in roots) or "none"
            message = (
                f"expected exactly one Contract Tree root; found {len(roots)} "
                f"unreferenced candidate(s): {root_names}"
            )
            if roots:
                for root_candidate in roots:
                    diagnostics.append(
                        Diagnostic(root_candidate.as_posix(), "contract.tree.root_count", message)
                    )
            else:
                # Every node has an incoming link - a pure cycle with no true root.
                diagnostics.append(
                    Diagnostic(tree_root.as_posix(), "contract.tree.root_count", message)
                )
        else:
            reachable: set[Path] = {roots[0]}
            frontier = [roots[0]]
            while frontier:
                current = frontier.pop()
                for child_path in resolved_children.get(current, []):
                    if child_path not in reachable:
                        reachable.add(child_path)
                        frontier.append(child_path)
            for node_path in sorted(normalized_by_path):
                if node_path not in reachable:
                    diagnostics.append(
                        Diagnostic(
                            node_path.as_posix(),
                            "contract.node.unreachable",
                            "Contract Node is not reachable from the tree root through "
                            "any section 2 child link",
                        )
                    )
    return ValidationResult(tuple(contracts), tuple(sorted(diagnostics)))


def build_tree_index(tree_root: str | Path) -> dict[str, dict[str, Any]]:
    """Discover every node in a valid Contract Tree, keyed by ``node_id`` (the
    path relative to ``tree_root``, POSIX-normalized). Each entry is the node's
    normalized contract dict plus ``node_id``, ``parent_id`` (``None`` at the
    root), and ``path`` (the resolved filesystem ``Path``).

    Refuses (raises ``ContractInstrumentError``) on an invalid tree rather than
    guess at structure - callers that need a durable index over this data
    (job-store, context-packer) share this one walk instead of each
    re-deriving parent/child relationships independently.
    """
    # Resolved up front so every path below is absolute: resolve_child_path() always
    # returns a resolved Path, and parent_of's membership check requires its keys to be
    # in the same form or a relative tree_root would silently match nothing, leaving
    # every non-root node's parent_id as None instead of raising.
    tree_root = Path(tree_root).resolve()
    result = validate_contract(tree_root)
    if not result.valid:
        raise ContractInstrumentError(
            f"cannot index an invalid Contract Tree: {result.diagnostics}"
        )
    paths = sorted(tree_root.rglob("SYSTEM.md"), key=lambda item: item.as_posix())
    if len(paths) != len(result.contracts):
        raise ContractInstrumentError("contract discovery and validation disagree on node count")
    contracts_by_path = dict(zip(paths, result.contracts, strict=True))
    node_ids = {path: path.relative_to(tree_root).as_posix() for path in paths}

    parent_of: dict[Path, Path | None] = dict.fromkeys(paths)
    for path, contract in contracts_by_path.items():
        if contract["atomic_leaf"]:
            continue
        for child_link in contract["children"]:
            child_path = resolve_child_path(path, child_link)
            if child_path in parent_of:
                parent_of[child_path] = path

    index: dict[str, dict[str, Any]] = {}
    for path in paths:
        node_id = node_ids[path]
        parent_path = parent_of[path]
        entry = dict(contracts_by_path[path])
        entry["node_id"] = node_id
        entry["parent_id"] = node_ids[parent_path] if parent_path is not None else None
        entry["path"] = path
        index[node_id] = entry
    return index
