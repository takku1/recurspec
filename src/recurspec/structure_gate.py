"""Deterministic source-to-contract structure policy."""

from __future__ import annotations

import ast
import re
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

_SECTION_SIX = re.compile(
    r"^## 6\.[^\n]*\n(?P<body>.*?)(?=^## [78]\.|\Z)",
    re.MULTILINE | re.DOTALL,
)
_SECTION_SEVEN = re.compile(
    r"^## 7\.[^\n]*\n(?P<body>.*?)(?=^## 8\.|\Z)",
    re.MULTILINE | re.DOTALL,
)
_BACKTICK = re.compile(r"`([^`]+)`")
_DECLARATION = re.compile(
    r"^- \*\*(?P<label>[^*]+):\*\*(?P<body>.*?)(?=^- \*\*|\Z)",
    re.MULTILINE | re.DOTALL,
)
_IMPLEMENTATION_LABELS = {
    "Implementation",
    "Implementation Files",
    "Current implementation",
    "Current prototype",
    "Package implementation glue",
}
_TEST_LABELS = {"Tests", "Test Surface Seam"}


class StructureParseError(Exception):
    """A language adapter could not parse a source file."""


@dataclass(frozen=True)
class LanguageAdapter:
    name: str
    glob: str
    public_symbols: Callable[[Path], list[str]]
    invalid_code: str = "structure.source.invalid"


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


def _is_contained(declared: str, repository: Path | None = None) -> bool:
    """True iff a §6-declared path stays inside the repository.

    A declaration is untrusted contract-author text, not code: a leading ``/``, a
    Windows drive letter, or a ``..`` segment must never be joined onto the repository
    root and used for I/O. Lexical containment is not enough: a repository-relative
    symlink whose resolved target leaves the tree is also unsafe.
    """
    if not declared or declared.startswith("/") or _DRIVE_LETTER_RE.match(declared):
        return False
    parts = PurePosixPath(declared).parts
    if ".." in parts:
        return False
    if repository is None:
        return True
    root = Path(repository).resolve()
    try:
        resolved = (root / declared).resolve()
    except OSError:
        return False
    return resolved.is_relative_to(root)


def _source_path_re(adapters: Sequence[LanguageAdapter]) -> re.Pattern[str]:
    extensions: list[str] = []
    for adapter in adapters:
        glob = adapter.glob
        if glob.startswith("*."):
            extensions.append(re.escape(glob[2:]))
    if not extensions:
        extensions = ["py"]
    return re.compile(r"`([^`]+\.(?:" + "|".join(extensions) + r"))`")


def declared_paths(
    contract: str | Path,
    repository: str | Path | None = None,
    *,
    adapters: Sequence[LanguageAdapter] | None = None,
) -> tuple[set[str], set[str], set[str]]:
    """Return repository-relative implementation and test paths declared in §6, plus
    any declared path that fails repository containment."""
    contract = Path(contract)
    text = contract.read_text(encoding="utf-8")
    section = _SECTION_SIX.search(text)
    if section is None:
        return set(), set(), set()
    implementation: set[str] = set()
    tests: set[str] = set()
    unsafe: set[str] = set()
    repo = Path(repository) if repository is not None else None
    path_re = _source_path_re(adapters if adapters is not None else DEFAULT_ADAPTERS)
    for item in _DECLARATION.finditer(section.group("body")):
        label = item.group("label")
        body = item.group("body")
        if any(marker in body.lower() for marker in ("not yet built", "none yet")):
            continue
        if label not in _IMPLEMENTATION_LABELS and label not in _TEST_LABELS:
            continue
        raw_paths = {_relative_path(path) for path in path_re.findall(body)}
        safe_paths = {path for path in raw_paths if _is_contained(path, repo)}
        unsafe.update(raw_paths - safe_paths)
        if label in _IMPLEMENTATION_LABELS:
            implementation.update(safe_paths)
        else:
            tests.update(safe_paths)
    return implementation, tests, unsafe


def _qualify_probe_scripts(tokens: list[str]) -> list[str]:
    """Turn §7 backtick tokens into repository-relative script paths.

    A bare ``checks.sh`` or ``measure.sh`` inherits the directory of the most
    recent qualified script on the same node (the ``measure.sh`, `checks.sh`` idiom).
    """
    qualified: list[str] = []
    last_directory = ""
    for raw in tokens:
        token = _relative_path(raw.strip())
        if not token.endswith(".sh"):
            continue
        if "/" not in token:
            if last_directory:
                token = f"{last_directory}/{token}"
        else:
            last_directory = str(PurePosixPath(token).parent)
        qualified.append(token)
    return qualified


def declared_probe_paths(
    contract: str | Path, repository: str | Path | None = None
) -> tuple[set[str], set[str]]:
    """Return §7-declared probe scripts plus any that fail repository containment."""
    contract = Path(contract)
    text = contract.read_text(encoding="utf-8")
    section = _SECTION_SEVEN.search(text)
    if section is None:
        return set(), set()
    tokens = [match.group(1) for match in _BACKTICK.finditer(section.group("body"))]
    repo = Path(repository) if repository is not None else None
    safe: set[str] = set()
    unsafe: set[str] = set()
    for declared in _qualify_probe_scripts(tokens):
        if _is_contained(declared, repo):
            safe.add(declared)
        else:
            unsafe.add(declared)
    return safe, unsafe


def _extract_python_public_symbols(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    explicit_exports: list[str] | None = None
    symbols: list[str] = []
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            if not node.name.startswith("_"):
                symbols.append(node.name)
            continue
        if not isinstance(node, (ast.Assign, ast.AnnAssign)):
            continue
        targets = node.targets if isinstance(node, ast.Assign) else [node.target]
        if any(isinstance(target, ast.Name) and target.id == "__all__" for target in targets):
            value = node.value
            if isinstance(value, (ast.List, ast.Tuple)) and all(
                isinstance(item, ast.Constant) and isinstance(item.value, str)
                for item in value.elts
            ):
                explicit_exports = [item.value for item in value.elts]
                continue
        for target in targets:
            if isinstance(target, ast.Name) and not target.id.startswith("_"):
                symbols.append(target.id)
    return sorted(set(explicit_exports if explicit_exports is not None else symbols))


def _python_public_symbols(path: Path) -> list[str]:
    try:
        return _extract_python_public_symbols(path)
    except (SyntaxError, UnicodeError) as exc:
        raise StructureParseError(str(exc)) from exc


PYTHON_ADAPTER = LanguageAdapter(
    name="python",
    glob="*.py",
    public_symbols=_python_public_symbols,
    invalid_code="structure.python.invalid",
)
DEFAULT_ADAPTERS: tuple[LanguageAdapter, ...] = (PYTHON_ADAPTER,)


_RUST_PUB_ITEMS = frozenset(
    {
        "function_item",
        "struct_item",
        "enum_item",
        "trait_item",
        "const_item",
        "static_item",
        "type_item",
    }
)


def _import_rust_parser():
    import tree_sitter_rust
    from tree_sitter import Language, Parser

    return Parser(Language(tree_sitter_rust.language()))


def _rust_node_name(node, source: bytes) -> str | None:
    for child in node.children:
        if child.type in {"identifier", "type_identifier"}:
            return source[child.start_byte : child.end_byte].decode("utf-8")
    return None


def _rust_is_pub(node) -> bool:
    return any(child.type == "visibility_modifier" for child in node.children)


def _rust_attribute_is_cfg_test(node, source: bytes) -> bool:
    for child in node.children:
        if child.type != "attribute":
            continue
        name = None
        tree = None
        for part in child.children:
            if part.type == "identifier" and name is None:
                name = part
            elif part.type == "token_tree":
                tree = part
        if name is None or tree is None:
            continue
        if source[name.start_byte : name.end_byte] != b"cfg":
            continue
        idents = [part for part in tree.children if part.type == "identifier"]
        has_test = any(source[part.start_byte : part.end_byte] == b"test" for part in idents)
        has_not = any(source[part.start_byte : part.end_byte] == b"not" for part in idents)
        if has_test and not has_not:
            return True
    return False


def _rust_skip_cfg_test_mod(children, index: int, source: bytes) -> bool:
    node = children[index]
    if node.type != "mod_item":
        return False
    cursor = index - 1
    while cursor >= 0 and children[cursor].type in {
        "attribute_item",
        "line_comment",
        "block_comment",
    }:
        sibling = children[cursor]
        if sibling.type == "attribute_item" and _rust_attribute_is_cfg_test(sibling, source):
            return True
        cursor -= 1
    return False


def _rust_public_symbols(path: Path) -> list[str]:
    try:
        parser = _import_rust_parser()
        source = path.read_bytes()
    except ImportError as exc:
        raise StructureParseError("rust adapter requires recurspec[rust]") from exc
    except OSError as exc:
        raise StructureParseError(str(exc)) from exc
    tree = parser.parse(source)
    names: list[str] = []
    children = tree.root_node.children
    for index, node in enumerate(children):
        if _rust_skip_cfg_test_mod(children, index, source):
            continue
        if node.type not in _RUST_PUB_ITEMS or not _rust_is_pub(node):
            continue
        name = _rust_node_name(node, source)
        if name:
            names.append(name)
    return sorted(set(names))


RUST_ADAPTER = LanguageAdapter(
    name="rust",
    glob="*.rs",
    public_symbols=_rust_public_symbols,
    invalid_code="structure.rust.invalid",
)


def rust_adapter() -> LanguageAdapter | None:
    try:
        _import_rust_parser()
    except ImportError:
        return None
    return RUST_ADAPTER


def available_adapters() -> tuple[LanguageAdapter, ...]:
    """Adapters whose runtime dependency is importable."""
    adapters: list[LanguageAdapter] = [PYTHON_ADAPTER]
    rust = rust_adapter()
    if rust is not None:
        adapters.append(rust)
    return tuple(adapters)


_NON_PACKAGE_DIRS = frozenset({"tests", "docs", "examples", "modules", "scripts"})


def infer_source_root(repository: str | Path) -> str | None:
    """Best-effort repository-relative source root: the one importable package.

    Returns ``None`` rather than guessing when the layout is ambiguous, so callers fail
    closed and name ``--source-root`` instead of auditing the wrong tree. Defaulting to
    a fixed path made both structure gates usable only inside Recurspec itself (R-701).
    """
    root = Path(repository).resolve()
    source = root / "src"
    if source.is_dir():
        # No __init__.py requirement: PEP 420 namespace packages legitimately lack one.
        packages = sorted(
            child.name
            for child in source.iterdir()
            if child.is_dir()
            and not child.name.startswith((".", "_"))
            and not child.name.endswith((".egg-info", ".dist-info"))
        )
        return f"src/{packages[0]}" if len(packages) == 1 else None
    packages = sorted(
        child.name
        for child in root.iterdir()
        if child.is_dir()
        and not child.name.startswith((".", "_"))
        and child.name not in _NON_PACKAGE_DIRS
        and (child / "__init__.py").is_file()
    )
    return packages[0] if len(packages) == 1 else None


def check_structure(
    repository: str | Path,
    *,
    source_root: str | Path | None = None,
    contract_root: str | Path = "docs/architecture",
    test_root: str | Path = "tests",
    changed_files: set[str] | None = None,
    adapters: Sequence[LanguageAdapter] | None = None,
) -> StructureResult:
    """Check that source is owned by Contract Node §6 declarations.

    ``changed_files`` narrows source inspection for pre-commit use while declarations are
    still validated globally. Paths are repository-relative and diagnostics are stable.
    Default adapters are Python-only so existing Python checks stay identical.
    """
    active = tuple(adapters) if adapters is not None else DEFAULT_ADAPTERS
    if source_root is None:
        source_root = infer_source_root(repository) or "src"
    root = Path(repository).resolve()
    source = (root / source_root).resolve()
    contracts = (root / contract_root).resolve()
    tests_root = (root / test_root).resolve()
    diagnostics: list[StructureDiagnostic] = []
    owners: dict[str, list[str]] = {}
    tests_for_implementation: dict[str, set[str]] = {}
    declared_tests: set[str] = set()

    # Reject a root override that escapes the repository before any relative_to(root)
    # call downstream can raise uncaught.
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
                "source root does not exist; pass --source-root to name it",
            )
        )
    if diagnostics:
        return StructureResult(tuple(sorted(diagnostics)), instrument_error=True)

    for contract in sorted(contracts.rglob("SYSTEM.md")):
        contract_name = contract.relative_to(root).as_posix()
        implementations, tests, unsafe = declared_paths(
            contract, repository=root, adapters=active
        )
        probes, unsafe_probes = declared_probe_paths(contract, repository=root)
        declared_tests.update(tests)
        for declared in sorted(unsafe | unsafe_probes):
            diagnostics.append(
                StructureDiagnostic(
                    "structure.declaration.unsafe_path",
                    declared,
                    f"{contract_name} declares a path that escapes the repository",
                )
            )
        for declared in sorted(probes):
            if not (root / declared).is_file():
                diagnostics.append(
                    StructureDiagnostic(
                        "structure.probe.missing",
                        declared,
                        f"{contract_name} declares a missing evaluation probe",
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
    seen_source: set[str] = set()
    for adapter in active:
        for path in sorted(source.rglob(adapter.glob)):
            relative = path.relative_to(root).as_posix()
            if relative in seen_source:
                continue
            seen_source.add(relative)
            if selected is not None and relative not in selected:
                continue
            try:
                symbols = adapter.public_symbols(path)
            except StructureParseError as error:
                instrument_error = True
                diagnostics.append(
                    StructureDiagnostic(
                        adapter.invalid_code,
                        relative,
                        f"cannot parse {adapter.name} source: {error}",
                    )
                )
                continue
            if relative in owners:
                if symbols and not tests_for_implementation.get(relative):
                    diagnostics.extend(
                        StructureDiagnostic(
                            "structure.public.untested",
                            relative,
                            "public symbol belongs to a Contract Node "
                            "with no declared test surface",
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
        seen_tests: set[str] = set()
        for adapter in active:
            for path in sorted(tests_root.rglob(adapter.glob)):
                relative = path.relative_to(root).as_posix()
                if relative in seen_tests:
                    continue
                seen_tests.add(relative)
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
