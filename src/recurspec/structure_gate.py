"""Deterministic source-to-contract structure policy."""

from __future__ import annotations

import ast
import re
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

_SECTION_SIX = re.compile(
    r"^## 6\.[^\n]*\n(?P<body>.*?)(?=^## [78]\.|\Z)",
    re.MULTILINE | re.DOTALL,
)
_DECLARATION = re.compile(
    r"^- \*\*(?P<label>[^*]+):\*\*(?P<body>.*?)(?=^- \*\*|\Z)",
    re.MULTILINE | re.DOTALL,
)
_PATH = re.compile(r"`([^`]+\.py)`")
_IMPLEMENTATION_LABELS = {
    "Implementation",
    "Implementation Files",
    "Current implementation",
    "Current prototype",
    "Package implementation glue",
}
_TEST_LABELS = {"Tests", "Test Surface Seam"}


@dataclass(frozen=True, order=True)
class StructureDiagnostic:
    code: str
    path: str
    message: str
    symbol: str | None = None

    def as_dict(self) -> dict[str, str | None]:
        return {
            "code": self.code,
            "message": self.message,
            "path": self.path,
            "symbol": self.symbol,
        }


@dataclass(frozen=True)
class StructureResult:
    diagnostics: tuple[StructureDiagnostic, ...]
    instrument_error: bool = False

    @property
    def valid(self) -> bool:
        return not self.diagnostics


_DRIVE_LETTER_RE = re.compile(r"^[A-Za-z]:")


def _relative_path(value: str) -> str:
    return PurePosixPath(value.replace("\\", "/")).as_posix()


def _is_contained(declared: str) -> bool:
    """True iff a §6-declared path is a genuine repository-relative path (R-608).

    A declaration is untrusted contract-author text, not code: a leading ``/``, a
    Windows drive letter, or a ``..`` segment must never be joined onto the repository
    root and used for I/O, because ``Path(root) / "/etc/passwd.py"`` (or a drive-letter
    path on Windows) discards ``root`` entirely rather than raising, and a ``..`` prefix
    resolves outside it - either way a Contract Node could claim ownership of, or point
    a "missing" check at, a file that was never part of the checked repository.
    """
    if not declared or declared.startswith("/") or _DRIVE_LETTER_RE.match(declared):
        return False
    parts = PurePosixPath(declared).parts
    return ".." not in parts


def declared_paths(contract: str | Path) -> tuple[set[str], set[str], set[str]]:
    """Return repository-relative implementation and test paths declared in §6, plus
    any declared path that fails repository containment (R-608)."""
    contract = Path(contract)
    text = contract.read_text(encoding="utf-8")
    section = _SECTION_SIX.search(text)
    if section is None:
        return set(), set(), set()
    implementation: set[str] = set()
    tests: set[str] = set()
    unsafe: set[str] = set()
    for item in _DECLARATION.finditer(section.group("body")):
        label = item.group("label")
        body = item.group("body")
        if any(marker in body.lower() for marker in ("not yet built", "none yet")):
            continue
        if label not in _IMPLEMENTATION_LABELS and label not in _TEST_LABELS:
            continue
        raw_paths = {_relative_path(path) for path in _PATH.findall(body)}
        safe_paths = {path for path in raw_paths if _is_contained(path)}
        unsafe.update(raw_paths - safe_paths)
        if label in _IMPLEMENTATION_LABELS:
            implementation.update(safe_paths)
        else:
            tests.update(safe_paths)
    return implementation, tests, unsafe


def _public_symbols(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    explicit_exports: list[str] | None = None
    symbols: list[str] = []
    for node in tree.body:
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            if any(isinstance(target, ast.Name) and target.id == "__all__" for target in targets):
                value = node.value
                if isinstance(value, (ast.List, ast.Tuple)) and all(
                    isinstance(item, ast.Constant) and isinstance(item.value, str)
                    for item in value.elts
                ):
                    explicit_exports = [item.value for item in value.elts]
                    continue
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            if not node.name.startswith("_"):
                symbols.append(node.name)
        elif isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            for target in targets:
                if isinstance(target, ast.Name) and not target.id.startswith("_"):
                    symbols.append(target.id)
    return sorted(set(explicit_exports if explicit_exports is not None else symbols))


def check_structure(
    repository: str | Path,
    *,
    source_root: str | Path = "src/recurspec",
    contract_root: str | Path = "docs/architecture",
    test_root: str | Path = "tests",
    changed_files: set[str] | None = None,
) -> StructureResult:
    """Check that Python source is owned by Contract Node §6 declarations.

    ``changed_files`` narrows source inspection for pre-commit use while declarations are
    still validated globally. Paths are repository-relative and diagnostics are stable.
    """
    root = Path(repository).resolve()
    source = (root / source_root).resolve()
    contracts = (root / contract_root).resolve()
    tests_root = (root / test_root).resolve()
    diagnostics: list[StructureDiagnostic] = []
    owners: dict[str, list[str]] = {}
    tests_for_implementation: dict[str, set[str]] = {}
    declared_tests: set[str] = set()

    # Reject a root override that escapes the repository before any relative_to(root)
    # call downstream can raise uncaught (R-608).
    for label, declared, resolved in (
        ("source_root", source_root, source),
        ("contract_root", contract_root, contracts),
        ("test_root", test_root, tests_root),
    ):
        if not resolved.is_relative_to(root):
            diagnostics.append(
                StructureDiagnostic(
                    f"structure.{label}.outside_repository",
                    Path(declared).as_posix(),
                    f"{label} resolves outside the repository root",
                )
            )
    if diagnostics:
        return StructureResult(tuple(sorted(diagnostics)), instrument_error=True)

    if not contracts.is_dir():
        diagnostics.append(
            StructureDiagnostic(
                "structure.contract_root.missing",
                Path(contract_root).as_posix(),
                "Contract Tree root does not exist",
            )
        )
    if not source.is_dir():
        diagnostics.append(
            StructureDiagnostic(
                "structure.source_root.missing",
                Path(source_root).as_posix(),
                "source root does not exist",
            )
        )
    if diagnostics:
        return StructureResult(tuple(sorted(diagnostics)), instrument_error=True)

    for contract in sorted(contracts.rglob("SYSTEM.md")):
        contract_name = contract.relative_to(root).as_posix()
        implementations, tests, unsafe = declared_paths(contract)
        declared_tests.update(tests)
        for declared in sorted(unsafe):
            diagnostics.append(
                StructureDiagnostic(
                    "structure.declaration.unsafe_path",
                    declared,
                    f"{contract_name} declares a path that escapes the repository",
                )
            )
        for declared in sorted(implementations):
            owners.setdefault(declared, []).append(contract_name)
            tests_for_implementation.setdefault(declared, set()).update(tests)
            if not (root / declared).is_file():
                diagnostics.append(
                    StructureDiagnostic(
                        "structure.implementation.missing",
                        declared,
                        f"{contract_name} declares a missing implementation",
                    )
                )
        for declared in sorted(tests):
            if not (root / declared).is_file():
                diagnostics.append(
                    StructureDiagnostic(
                        "structure.test_surface.missing",
                        declared,
                        f"{contract_name} declares a missing test surface",
                    )
                )

    for declared, contract_names in sorted(owners.items()):
        if len(contract_names) > 1:
            diagnostics.append(
                StructureDiagnostic(
                    "structure.implementation.ambiguous",
                    declared,
                    "implementation is claimed by multiple Contract Nodes: "
                    + ", ".join(contract_names),
                )
            )

    instrument_error = False
    selected = {_relative_path(path) for path in changed_files} if changed_files else None
    for path in sorted(source.rglob("*.py")):
        relative = path.relative_to(root).as_posix()
        if selected is not None and relative not in selected:
            continue
        try:
            symbols = _public_symbols(path)
        except (SyntaxError, UnicodeError) as error:
            instrument_error = True
            diagnostics.append(
                StructureDiagnostic(
                    "structure.python.invalid", relative, f"cannot parse Python source: {error}"
                )
            )
            continue
        if relative in owners:
            if symbols and not tests_for_implementation.get(relative):
                diagnostics.extend(
                    StructureDiagnostic(
                        "structure.public.untested",
                        relative,
                        "public symbol belongs to a Contract Node with no declared test surface",
                        symbol,
                    )
                    for symbol in symbols
                )
            continue
        if symbols:
            diagnostics.extend(
                StructureDiagnostic(
                    "structure.public.uncontracted",
                    relative,
                    "public symbol has no parent Contract Node",
                    symbol,
                )
                for symbol in symbols
            )
        else:
            diagnostics.append(
                StructureDiagnostic(
                    "structure.source.uncontracted",
                    relative,
                    "source file has no parent Contract Node",
                )
            )

    if tests_root.is_dir():
        for path in sorted(tests_root.rglob("*.py")):
            relative = path.relative_to(root).as_posix()
            if selected is not None and relative not in selected:
                continue
            if relative not in declared_tests:
                diagnostics.append(
                    StructureDiagnostic(
                        "structure.test.uncontracted",
                        relative,
                        "test file is not declared by a Contract Node",
                    )
                )

    return StructureResult(tuple(sorted(diagnostics)), instrument_error=instrument_error)
