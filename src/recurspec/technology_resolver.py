"""Deterministic audits for Technology Resolution completeness and staleness."""

from __future__ import annotations

import json
import re
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any

from .contract import ContractInstrumentError, build_tree_index, decision_class
from .structure_gate import declared_paths

_FIELD = re.compile(
    r"^\s*-\s+\*\*(?P<label>[^*]+):\*\*\s*(?P<body>.*?)(?=^\s*-\s+\*\*|\Z)",
    re.MULTILINE | re.DOTALL,
)
_PATH = re.compile(r"`([^`]+\.py)`")
_QUOTED_PATH = re.compile(r"`([^`]+)`")
_REQUIRED_FIELDS = {
    "Alternatives considered",
    "Cost model",
    "Decision class",
    "Exit cost",
    "Failure mode",
    "Fit gap",
    "Liability transferred",
    "Open questions",
    "Operational owner",
    "Seam",
    "Selected",
    "Standard / protocol",
}
_PROCURED_CLASSES = {"BUY", "ADOPT", "WRAP"}
_DEFER_MARKERS = {"defer", "none", "not selected", "pending", "research", "review", "unresolved"}


class ResolutionInstrumentError(RuntimeError):
    """The Contract Tree could not be audited without guessing."""


@dataclass(frozen=True, order=True)
class ResolutionDiagnostic:
    code: str
    path: str
    message: str

    def as_dict(self) -> dict[str, str]:
        return {"code": self.code, "message": self.message, "path": self.path}


@dataclass(frozen=True)
class ResolutionAudit:
    diagnostics: tuple[ResolutionDiagnostic, ...]
    completeness: float
    indeterminate: bool = False

    @property
    def valid(self) -> bool:
        return not self.diagnostics and not self.indeterminate

    def as_dict(self) -> dict[str, Any]:
        return {
            "completeness": self.completeness,
            "diagnostics": [item.as_dict() for item in self.diagnostics],
            "indeterminate": self.indeterminate,
            "valid": self.valid,
        }


def _fields(section: str) -> dict[str, str]:
    return {
        match.group("label").strip(): match.group("body").strip()
        for match in _FIELD.finditer(section)
    }


def _plain(value: str) -> str:
    return value.strip().strip("`.").strip()


def _normalize_dependency(value: str) -> str:
    return re.sub(r"[-_.]+", "-", value).lower()


def _repository_path(root: Path, contract_root: str | Path) -> Path:
    path = Path(contract_root)
    return path.resolve() if path.is_absolute() else (root / path).resolve()


_FLOATING_MARKERS = {
    "latest",
    "*",
    "master",
    "main",
    "head",
    "stable",
    "unstable",
    "snapshot",
    "nightly",
    "edge",
    "canary",
    "trunk",
    "dev",
}
_RANGE_OPERATOR_RE = re.compile(r"[<>=~^!,\s]")
# Semver-shaped (optionally v-prefixed) exact version: "1.2.3", "v1.2.3", "1.2.3-rc.1",
# "1.2.3+build.5". The numeric core is digits-only and dot-separated (so "1latest" and
# "1.foo" cannot pass as a version); a non-numeric component is only permitted inside an
# explicit "-prerelease" or "+build" suffix, matching where semver actually allows one
# (R-622, R-642).
_SEMVER_RE = re.compile(r"^v?[0-9]+(?:\.[0-9]+){0,2}(?:-[0-9A-Za-z.]+)?(?:\+[0-9A-Za-z.]+)?$")
# An immutable git/VCS revision - short or full hex SHA. Must contain a letter so a
# plain numeric version (e.g. a build number) is never mistaken for one.
_HEX_REVISION_RE = re.compile(r"^[0-9a-fA-F]{7,64}$")
# An immutable content digest, e.g. an OCI/Docker pin: "sha256:<hex>".
_DIGEST_RE = re.compile(r"^[A-Za-z][A-Za-z0-9]*:[0-9a-fA-F]{32,}$")


def _looks_exact(version: str) -> bool:
    """Reject known floating/range specifiers and malformed strings, while accepting
    ecosystem-valid immutable versions, v-prefixed tags, digests, and revisions, so
    'exact-version' inventories and pins cannot both float to the same string and read
    as a reproducible pin - nor be rejected merely for using a real exact form the
    original digit-only pattern did not recognize (R-607)."""
    value = version.strip()
    if not value:
        return False
    lowered = value.lower()
    if lowered in _FLOATING_MARKERS:
        return False
    if _RANGE_OPERATOR_RE.search(value):
        return False
    if lowered == "x" or lowered.endswith(".x") or ".x." in lowered:
        return False
    if ".." in value or value[0] in ".-_" or value[-1] in ".-_":
        return False
    if _DIGEST_RE.match(value):
        return True
    if _HEX_REVISION_RE.match(value) and any(c in "abcdefABCDEF" for c in value):
        return True
    return bool(_SEMVER_RE.match(value))


def load_dependency_inventory(path: str | Path) -> dict[str, str]:
    """Load an authoritative JSON ``{normalized-package: exact-version}`` inventory."""
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or not all(
        isinstance(name, str) and isinstance(version, str) and name and version
        for name, version in payload.items()
    ):
        raise ResolutionInstrumentError(
            "dependency inventory must be a JSON object of non-empty string names and versions"
        )
    floating = sorted(name for name, version in payload.items() if not _looks_exact(version))
    if floating:
        raise ResolutionInstrumentError(
            "dependency inventory must record exact versions, not floating constraints: "
            + ", ".join(f"{name}={payload[name]!r}" for name in floating)
        )
    return {_normalize_dependency(name): version for name, version in payload.items()}


def audit_resolutions(
    repository: str | Path,
    *,
    contract_root: str | Path = "docs/architecture",
    inventory: Mapping[str, str] | None = None,
    wrap_line_limit: int = 150,
) -> ResolutionAudit:
    """Audit terminal §8 blocks against declared seams and an authoritative inventory."""
    if wrap_line_limit < 1:
        raise ValueError("wrap_line_limit must be positive")
    root = Path(repository).resolve()
    tree = _repository_path(root, contract_root)
    if not tree.is_relative_to(root):
        raise ResolutionInstrumentError(
            f"contract_root {contract_root!r} resolves outside the repository root"
        )
    try:
        index = build_tree_index(tree)
    except ContractInstrumentError as exc:
        raise ResolutionInstrumentError(str(exc)) from exc

    diagnostics: list[ResolutionDiagnostic] = []
    required_slots = 0
    populated_slots = 0
    indeterminate = False

    for _node_id, node in sorted(index.items()):
        if not node["atomic_leaf"]:
            continue
        contract_path = Path(node["path"])
        display_path = contract_path.relative_to(root).as_posix()
        section = node["sections"].get("8", "")
        fields = _fields(section)
        node_class = decision_class(node["sections"])
        required = set(_REQUIRED_FIELDS)
        if node_class == "BUILD":
            required.add("Justification")
        required_slots += len(required)
        populated_slots += sum(bool(fields.get(field, "").strip()) for field in required)
        for field in sorted(required):
            if not fields.get(field, "").strip():
                diagnostics.append(
                    ResolutionDiagnostic(
                        "resolution.field.missing",
                        display_path,
                        f"Technology Resolution is missing {field!r}",
                    )
                )

        if node_class == "DEFER":
            selected = fields.get("Selected", "").lower()
            if selected and not any(marker in selected for marker in _DEFER_MARKERS):
                diagnostics.append(
                    ResolutionDiagnostic(
                        "resolution.defer.vendor_selected",
                        display_path,
                        "DEFER cannot name a selected vendor without completed evidence",
                    )
                )
            open_questions = fields.get("Open questions", "")
            if not re.search(r"\bR-\d+\b", open_questions, re.IGNORECASE):
                diagnostics.append(
                    ResolutionDiagnostic(
                        "resolution.defer.ticket_missing",
                        display_path,
                        "DEFER requires a Research Frontier reference (ROADMAP R-nnn)",
                    )
                )
            continue

        if node_class in _PROCURED_CLASSES:
            pin = _plain(fields.get("Pin", ""))
            dependency = _normalize_dependency(_plain(fields.get("Dependency", "")))
            standard_library = pin.lower().startswith("none") and "standard library" in fields.get(
                "Selected", ""
            ).lower()
            if not standard_library and (not pin or not dependency):
                missing = " and ".join(
                    label
                    for label, value in (("Dependency", dependency), ("Pin", pin))
                    if not value
                )
                diagnostics.append(
                    ResolutionDiagnostic(
                        "resolution.pin.missing",
                        display_path,
                        f"external {node_class} resolution is missing {missing}",
                    )
                )
            elif not standard_library and not _looks_exact(pin):
                diagnostics.append(
                    ResolutionDiagnostic(
                        "resolution.pin.not_exact",
                        display_path,
                        f"§8 Pin {pin!r} is not an exact, reproducible version",
                    )
                )
            elif not standard_library:
                if inventory is None:
                    indeterminate = True
                    diagnostics.append(
                        ResolutionDiagnostic(
                            "resolution.inventory.unavailable",
                            display_path,
                            f"cannot verify {dependency!r} pin without an authoritative inventory",
                        )
                    )
                else:
                    installed = inventory.get(dependency)
                    if installed is None:
                        diagnostics.append(
                            ResolutionDiagnostic(
                                "resolution.dependency.unlocked",
                                display_path,
                                f"dependency {dependency!r} is absent from the inventory",
                            )
                        )
                    elif _plain(str(installed)) != pin:
                        diagnostics.append(
                            ResolutionDiagnostic(
                                "resolution.pin.stale",
                                display_path,
                                f"§8 pins {dependency} {pin}, inventory records {installed}",
                            )
                        )

        if node_class == "WRAP":
            seam_paths = {
                PurePosixPath(path.replace("\\", "/")).as_posix()
                for path in _PATH.findall(fields.get("Seam", ""))
            }
            implementations, _, _ = declared_paths(contract_path)
            namespaces = {
                PurePosixPath(path.replace("\\", "/")).as_posix().rstrip("/")
                for path in _QUOTED_PATH.findall(fields.get("Adapter namespace", ""))
            }
            if not namespaces:
                diagnostics.append(
                    ResolutionDiagnostic(
                        "resolution.wrap.namespace_missing",
                        display_path,
                        "WRAP requires an Adapter namespace for undeclared-growth detection",
                    )
                )
            namespace_files: set[str] = set()
            for namespace in namespaces:
                directory = root / namespace
                if not directory.is_dir():
                    diagnostics.append(
                        ResolutionDiagnostic(
                            "resolution.wrap.namespace_missing",
                            display_path,
                            f"declared Adapter namespace {namespace!r} does not exist",
                        )
                    )
                    continue
                namespace_files.update(
                    path.relative_to(root).as_posix() for path in directory.rglob("*.py")
                )
            spread = sorted((implementations | namespace_files) - seam_paths)
            if spread:
                diagnostics.append(
                    ResolutionDiagnostic(
                        "resolution.wrap.seam_spread",
                        display_path,
                        "WRAP implementation extends beyond its declared seam: "
                        + ", ".join(spread),
                    )
                )
            for seam in sorted(seam_paths):
                seam_file = root / seam
                if not seam_file.is_file():
                    continue
                content_lines = seam_file.read_text(encoding="utf-8").splitlines()
                lines = sum(bool(line.strip()) for line in content_lines)
                if lines > wrap_line_limit:
                    diagnostics.append(
                        ResolutionDiagnostic(
                            "resolution.wrap.bloat",
                            display_path,
                            f"WRAP seam {seam!r} has {lines} nonblank lines; "
                            f"limit is {wrap_line_limit}",
                        )
                    )

    completeness = populated_slots / required_slots if required_slots else 1.0
    return ResolutionAudit(tuple(sorted(diagnostics)), completeness, indeterminate)
