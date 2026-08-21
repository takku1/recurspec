from pathlib import Path

import pytest

from recurspec.structure_gate import (
    RUST_ADAPTER,
    LanguageAdapter,
    available_adapters,
    check_structure,
    declared_paths,
    declared_probe_paths,
    infer_source_root,
    rust_adapter,
    source_root_candidates,
)


def _contract(implementation: str, tests: str) -> str:
    return f"""# Example

## 6. Leaf Execution & Test Seam

- **Implementation:** `{implementation}`.
- **Tests:** `{tests}`.

## 7. Measurement Seams
"""


def test_structure_gate_accepts_contract_owned_python_with_a_real_test_surface(tmp_path: Path):
    source = tmp_path / "src" / "pkg" / "feature.py"
    test = tmp_path / "tests" / "test_feature.py"
    contract = tmp_path / "docs" / "architecture" / "feature" / "SYSTEM.md"
    source.parent.mkdir(parents=True)
    test.parent.mkdir(parents=True)
    contract.parent.mkdir(parents=True)
    source.write_text("def public_seam():\n    return 1\n", encoding="utf-8")
    test.write_text("def test_public_seam():\n    assert True\n", encoding="utf-8")
    contract.write_text(_contract("src/pkg/feature.py", "tests/test_feature.py"), encoding="utf-8")

    result = check_structure(tmp_path, source_root="src", contract_root="docs/architecture")

    assert result.valid
    assert result.diagnostics == ()


def test_structure_gate_reports_each_public_symbol_in_an_uncontracted_source_file(tmp_path: Path):
    source = tmp_path / "src" / "pkg" / "orphan.py"
    contracts = tmp_path / "docs" / "architecture"
    source.parent.mkdir(parents=True)
    contracts.mkdir(parents=True)
    source.write_text("class PublicThing:\n    pass\n\ndef helper():\n    pass\n", encoding="utf-8")

    result = check_structure(tmp_path, source_root="src", contract_root="docs/architecture")

    assert not result.valid
    assert [(item.code, item.symbol) for item in result.diagnostics] == [
        ("structure.public.uncontracted", "PublicThing"),
        ("structure.public.uncontracted", "helper"),
    ]


def test_declared_probe_paths_resolves_a_bare_checks_sibling(tmp_path: Path):
    contract = tmp_path / "SYSTEM.md"
    contract.write_text(
        """# Example (L2)

## 7. Measurement Seams

- **Evaluation Gate / checks:** `modules/ingest-parse/measure.sh`, `checks.sh`
""",
        encoding="utf-8",
    )

    probes, unsafe = declared_probe_paths(contract, repository=tmp_path)

    assert unsafe == set()
    assert probes == {
        "modules/ingest-parse/measure.sh",
        "modules/ingest-parse/checks.sh",
    }


def test_declared_probe_paths_keeps_a_bare_script_as_repo_relative(tmp_path: Path):
    contract = tmp_path / "SYSTEM.md"
    contract.write_text(
        """# Example (L2)

## 7. Measurement Seams

- **Evaluation Gate:** `measure.sh`
""",
        encoding="utf-8",
    )

    probes, unsafe = declared_probe_paths(contract, repository=tmp_path)

    assert unsafe == set()
    assert probes == {"measure.sh"}


def test_structure_gate_reports_a_missing_declared_probe(tmp_path: Path):
    source = tmp_path / "src" / "pkg" / "feature.py"
    test = tmp_path / "tests" / "test_feature.py"
    contract = tmp_path / "docs" / "architecture" / "feature" / "SYSTEM.md"
    source.parent.mkdir(parents=True)
    test.parent.mkdir(parents=True)
    contract.parent.mkdir(parents=True)
    source.write_text("def public_seam():\n    return 1\n", encoding="utf-8")
    test.write_text("def test_public_seam():\n    assert True\n", encoding="utf-8")
    contract.write_text(
        _contract("src/pkg/feature.py", "tests/test_feature.py")
        + "\n- **Evaluation Gate:** `modules/feature/measure.sh`\n",
        encoding="utf-8",
    )

    result = check_structure(tmp_path, source_root="src", contract_root="docs/architecture")

    assert [item.code for item in result.diagnostics] == ["structure.probe.missing"]
    assert result.diagnostics[0].path == "modules/feature/measure.sh"


def test_structure_gate_reports_missing_declared_implementation_and_test_paths(tmp_path: Path):
    contract = tmp_path / "docs" / "architecture" / "feature" / "SYSTEM.md"
    (tmp_path / "src").mkdir()
    contract.parent.mkdir(parents=True)
    contract.write_text(_contract("src/pkg/missing.py", "tests/test_missing.py"), encoding="utf-8")

    result = check_structure(tmp_path, source_root="src", contract_root="docs/architecture")

    assert [item.code for item in result.diagnostics] == [
        "structure.implementation.missing",
        "structure.test_surface.missing",
    ]


def test_structure_gate_refuses_invalid_python_as_an_instrument_error(tmp_path: Path):
    source = tmp_path / "src" / "broken.py"
    contract = tmp_path / "docs" / "architecture" / "feature" / "SYSTEM.md"
    source.parent.mkdir()
    contract.parent.mkdir(parents=True)
    source.write_text("def nope(:\n", encoding="utf-8")
    contract.write_text(_contract("src/broken.py", "tests/test_broken.py"), encoding="utf-8")

    result = check_structure(tmp_path, source_root="src", contract_root="docs/architecture")

    assert not result.valid
    assert result.instrument_error
    assert result.diagnostics[0].code == "structure.python.invalid"


def test_structure_gate_refuses_missing_input_roots(tmp_path: Path):
    result = check_structure(tmp_path)

    assert result.instrument_error
    assert [item.code for item in result.diagnostics] == [
        "structure.contract_root.missing",
        "structure.source_root.missing",
    ]


def test_structure_gate_refuses_a_source_root_that_escapes_the_repository(tmp_path: Path):
    (tmp_path / "docs" / "architecture").mkdir(parents=True)

    result = check_structure(tmp_path, source_root="../../outside")

    assert result.instrument_error
    assert any(
        item.code == "structure.source_root.outside_repository" for item in result.diagnostics
    )


def test_structure_gate_rejects_a_declared_path_that_escapes_the_repository(tmp_path: Path):
    # A file that genuinely exists just outside the repository - if the contract's
    # escaping declaration were joined onto the root and checked as-is, this would read
    # as a *satisfied* implementation instead of an unsafe declaration (R-608).
    (tmp_path.parent / "outside.py").write_text("def public():\n    pass\n", encoding="utf-8")
    contract = tmp_path / "docs" / "architecture" / "feature" / "SYSTEM.md"
    (tmp_path / "src").mkdir()
    contract.parent.mkdir(parents=True)
    contract.write_text(
        _contract("../outside.py", "tests/test_missing.py"), encoding="utf-8"
    )

    result = check_structure(tmp_path, source_root="src", contract_root="docs/architecture")

    assert not result.valid
    unsafe = [
        item for item in result.diagnostics if item.code == "structure.declaration.unsafe_path"
    ]
    assert len(unsafe) == 1
    assert unsafe[0].path == "../outside.py"
    # The escaping declaration must not be treated as a satisfied implementation.
    assert not any(item.code == "structure.implementation.missing" for item in result.diagnostics)


def test_declared_paths_rejects_a_resolved_target_outside_the_repository(
    tmp_path: Path, monkeypatch
):
    repo = tmp_path / "repo"
    (repo / "src").mkdir(parents=True)
    (repo / "src" / "linked.py").write_text("def public():\n    pass\n", encoding="utf-8")
    contract = repo / "docs" / "architecture" / "feature" / "SYSTEM.md"
    contract.parent.mkdir(parents=True)
    contract.write_text(_contract("src/linked.py", "tests/test_missing.py"), encoding="utf-8")
    outside = (tmp_path / "outside.py").resolve()
    original = Path.resolve

    def fake_resolve(self, *args, **kwargs):
        if Path(self).as_posix().endswith("src/linked.py"):
            return outside
        return original(self, *args, **kwargs)

    monkeypatch.setattr(Path, "resolve", fake_resolve)
    implementations, _tests, unsafe = declared_paths(contract, repository=repo)

    assert "src/linked.py" in unsafe
    assert "src/linked.py" not in implementations


def test_structure_gate_rejects_a_symlink_whose_target_escapes_the_repository(
    tmp_path: Path,
):
    outside = tmp_path / "outside.py"
    outside.write_text("def public():\n    pass\n", encoding="utf-8")
    repo = tmp_path / "repo"
    source = repo / "src"
    source.mkdir(parents=True)
    linked = source / "linked.py"
    try:
        linked.symlink_to(outside)
    except OSError:
        import pytest

        pytest.skip("symlinks are not available on this platform")
    contract = repo / "docs" / "architecture" / "feature" / "SYSTEM.md"
    contract.parent.mkdir(parents=True)
    contract.write_text(_contract("src/linked.py", "tests/test_missing.py"), encoding="utf-8")

    result = check_structure(repo, source_root="src", contract_root="docs/architecture")

    assert any(
        item.code == "structure.declaration.unsafe_path" and item.path == "src/linked.py"
        for item in result.diagnostics
    )


def test_structure_gate_rejects_an_absolute_declared_path(tmp_path: Path):
    contract = tmp_path / "docs" / "architecture" / "feature" / "SYSTEM.md"
    (tmp_path / "src").mkdir()
    contract.parent.mkdir(parents=True)
    contract.write_text(_contract("/etc/passwd.py", "tests/test_missing.py"), encoding="utf-8")

    result = check_structure(tmp_path, source_root="src", contract_root="docs/architecture")

    assert not result.valid
    assert any(
        item.code == "structure.declaration.unsafe_path" and item.path == "/etc/passwd.py"
        for item in result.diagnostics
    )


def test_structure_gate_changed_files_narrows_source_drift_but_not_contract_drift(
    tmp_path: Path,
):
    source = tmp_path / "src"
    contracts = tmp_path / "docs" / "architecture" / "feature"
    source.mkdir()
    contracts.mkdir(parents=True)
    (source / "changed.py").write_text("def changed():\n    pass\n", encoding="utf-8")
    (source / "ignored.py").write_text("def ignored():\n    pass\n", encoding="utf-8")
    (contracts / "SYSTEM.md").write_text(
        _contract("src/missing.py", "tests/missing.py"), encoding="utf-8"
    )

    result = check_structure(
        tmp_path,
        source_root="src",
        contract_root="docs/architecture",
        changed_files={"src/changed.py"},
    )

    assert [item.code for item in result.diagnostics] == [
        "structure.implementation.missing",
        "structure.public.uncontracted",
        "structure.test_surface.missing",
    ]
    assert all(item.symbol != "ignored" for item in result.diagnostics)


def test_structure_gate_reports_an_uncontracted_test_surface(tmp_path: Path):
    source = tmp_path / "src" / "feature.py"
    test = tmp_path / "tests" / "test_extra.py"
    contract = tmp_path / "docs" / "architecture" / "feature" / "SYSTEM.md"
    source.parent.mkdir()
    test.parent.mkdir()
    contract.parent.mkdir(parents=True)
    source.write_text("def feature():\n    return True\n", encoding="utf-8")
    test.write_text("def test_extra():\n    assert True\n", encoding="utf-8")
    contract.write_text(_contract("src/feature.py", "tests/test_feature.py"), encoding="utf-8")
    (tmp_path / "tests" / "test_feature.py").write_text("def test_feature():\n    pass\n")

    result = check_structure(tmp_path, source_root="src", contract_root="docs/architecture")

    assert "structure.test.uncontracted" in {item.code for item in result.diagnostics}


def test_structure_gate_uses_explicit_exports_and_requires_their_test_surface(tmp_path: Path):
    source = tmp_path / "src" / "feature.py"
    contract = tmp_path / "docs" / "architecture" / "feature" / "SYSTEM.md"
    source.parent.mkdir()
    contract.parent.mkdir(parents=True)
    source.write_text(
        '__all__ = ["exported"]\n\n'
        "def exported():\n    pass\n\n"
        "def public_but_not_exported():\n    pass\n",
        encoding="utf-8",
    )
    contract.write_text(_contract("src/feature.py", "none yet"), encoding="utf-8")

    result = check_structure(tmp_path, source_root="src", contract_root="docs/architecture")

    assert [(item.code, item.symbol) for item in result.diagnostics] == [
        ("structure.public.untested", "exported")
    ]


def test_default_adapters_ignore_non_python_source(tmp_path: Path):
    source = tmp_path / "src" / "pkg"
    source.mkdir(parents=True)
    (source / "feature.py").write_text("def public_seam():\n    return 1\n", encoding="utf-8")
    (source / "lib.rs").write_text("pub fn leftover() {}\n", encoding="utf-8")
    test = tmp_path / "tests" / "test_feature.py"
    test.parent.mkdir()
    test.write_text("def test_public_seam():\n    assert True\n", encoding="utf-8")
    contract = tmp_path / "docs" / "architecture" / "feature" / "SYSTEM.md"
    contract.parent.mkdir(parents=True)
    contract.write_text(_contract("src/pkg/feature.py", "tests/test_feature.py"), encoding="utf-8")

    result = check_structure(tmp_path, source_root="src", contract_root="docs/architecture")

    assert result.valid
    assert all("lib.rs" not in item.path for item in result.diagnostics)


def test_check_structure_uses_an_injected_language_adapter(tmp_path: Path):
    source = tmp_path / "src" / "pkg" / "lib.rs"
    source.parent.mkdir(parents=True)
    source.write_text("pub fn leftover() {}\n", encoding="utf-8")
    (tmp_path / "docs" / "architecture").mkdir(parents=True)
    adapter = LanguageAdapter(
        name="rust",
        glob="*.rs",
        public_symbols=lambda _path: ["leftover"],
    )

    result = check_structure(
        tmp_path,
        source_root="src",
        contract_root="docs/architecture",
        adapters=(adapter,),
    )

    assert [(item.code, item.symbol) for item in result.diagnostics] == [
        ("structure.public.uncontracted", "leftover")
    ]


def test_declared_paths_matches_injected_adapter_extensions(tmp_path: Path):
    contract = tmp_path / "SYSTEM.md"
    contract.write_text(
        """# Example

## 6. Leaf Execution & Test Seam

- **Implementation:** `src/pkg/lib.rs`.
- **Tests:** `tests/lib.rs`.
""",
        encoding="utf-8",
    )
    adapter = LanguageAdapter(
        name="rust",
        glob="*.rs",
        public_symbols=lambda _path: [],
    )

    implementations, tests, unsafe = declared_paths(
        contract, repository=tmp_path, adapters=(adapter,)
    )

    assert unsafe == set()
    assert implementations == {"src/pkg/lib.rs"}
    assert tests == {"tests/lib.rs"}
    default_impl, default_tests, _unsafe = declared_paths(contract, repository=tmp_path)
    assert default_impl == set()
    assert default_tests == set()


_RUST_FIXTURE = """
pub fn visible() {}
fn hidden() {}
pub struct Visible {}
pub enum Kind { A }
#[cfg(test)]
mod tests {
    pub fn test_only() {}
}
"""


def test_rust_adapter_detects_pub_items_and_skips_cfg_test(tmp_path: Path):
    pytest.importorskip("tree_sitter_rust")
    source = tmp_path / "src" / "pkg" / "lib.rs"
    test = tmp_path / "tests" / "lib.rs"
    contract = tmp_path / "docs" / "architecture" / "feature" / "SYSTEM.md"
    source.parent.mkdir(parents=True)
    test.parent.mkdir(parents=True)
    contract.parent.mkdir(parents=True)
    source.write_text(_RUST_FIXTURE, encoding="utf-8")
    test.write_text("fn helper() {}\n", encoding="utf-8")
    contract.write_text(
        """# Example

## 6. Leaf Execution & Test Seam

- **Implementation:** `src/pkg/lib.rs`.
- **Tests:** `tests/lib.rs`.
""",
        encoding="utf-8",
    )

    result = check_structure(
        tmp_path,
        source_root="src",
        contract_root="docs/architecture",
        adapters=(RUST_ADAPTER,),
    )

    assert result.valid
    symbols = RUST_ADAPTER.public_symbols(source)
    assert symbols == ["Kind", "Visible", "visible"]
    assert "test_only" not in symbols
    assert "hidden" not in symbols


def test_rust_adapter_reports_a_missing_declared_rust_test_file(tmp_path: Path):
    pytest.importorskip("tree_sitter_rust")
    source = tmp_path / "src" / "pkg" / "lib.rs"
    contract = tmp_path / "docs" / "architecture" / "feature" / "SYSTEM.md"
    source.parent.mkdir(parents=True)
    contract.parent.mkdir(parents=True)
    source.write_text("pub fn visible() {}\n", encoding="utf-8")
    contract.write_text(
        """# Example

## 6. Leaf Execution & Test Seam

- **Implementation:** `src/pkg/lib.rs`.
- **Tests:** `tests/lib.rs`.
""",
        encoding="utf-8",
    )

    result = check_structure(
        tmp_path,
        source_root="src",
        contract_root="docs/architecture",
        adapters=(RUST_ADAPTER,),
    )

    assert [item.code for item in result.diagnostics] == ["structure.test_surface.missing"]
    assert result.diagnostics[0].path == "tests/lib.rs"


def test_available_adapters_omits_rust_when_the_extra_is_missing(monkeypatch):
    import recurspec.structure_gate as gate

    def missing():
        raise ImportError("recurspec[rust] is not installed")

    monkeypatch.setattr(gate, "_import_rust_parser", missing)
    assert rust_adapter() is None
    assert all(adapter.name != "rust" for adapter in available_adapters())
    assert available_adapters()[0].name == "python"


def test_source_root_is_inferred_from_the_repository_layout(tmp_path: Path):
    """The gates must work on a repository that is not Recurspec itself (R-701)."""
    package = tmp_path / "src" / "someproject"
    package.mkdir(parents=True)
    (tmp_path / "src" / "someproject.egg-info").mkdir()

    assert infer_source_root(tmp_path) == "src/someproject"


def test_source_root_inference_declines_an_ambiguous_layout(tmp_path: Path):
    for name in ("alpha", "beta"):
        (tmp_path / "src" / name).mkdir(parents=True)

    assert infer_source_root(tmp_path) is None


def test_source_root_inference_finds_a_flat_layout_package(tmp_path: Path):
    package = tmp_path / "someproject"
    package.mkdir()
    (package / "__init__.py").write_text("", encoding="utf-8")
    (tmp_path / "tests").mkdir()
    (tmp_path / "docs").mkdir()

    assert infer_source_root(tmp_path) == "someproject"


def test_ambiguous_source_root_fails_closed_naming_the_flag(tmp_path: Path):
    """infer_source_root promises callers fail closed on ambiguity; they used to fall
    back to "src" and audit both packages instead (R-701)."""
    for name in ("alpha", "beta"):
        (tmp_path / "src" / name).mkdir(parents=True)
    (tmp_path / "docs" / "architecture").mkdir(parents=True)

    assert source_root_candidates(tmp_path) == ["src/alpha", "src/beta"]
    result = check_structure(tmp_path)

    diagnostic = next(
        item for item in result.diagnostics if item.code == "structure.source_root.ambiguous"
    )
    assert "--source-root" in diagnostic.message


def test_section_six_examples_inside_a_fence_are_not_declared_paths(tmp_path: Path):
    """declared_paths harvested a fenced example as a real declaration, so the gate
    could believe a nonexistent file was covered (R-701)."""
    fence = "`" * 3
    lines = [
        "# X (L1)",
        "",
        "## 6. Leaf Execution & Test Seam",
        "",
        "- **Implementation Files:** `src/real.py`.",
        "- **Test Surface Seam:** `tests/test_real.py`.",
        "",
        fence + "markdown",
        "- **Implementation Files:** `src/example_only.py`.",
        fence,
    ]
    contract = tmp_path / "SYSTEM.md"
    contract.write_text(chr(10).join(lines), encoding="utf-8")

    implementations, tests, _ = declared_paths(contract)

    assert implementations == {"src/real.py"}
    assert tests == {"tests/test_real.py"}
