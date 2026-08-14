from pathlib import Path

from recurspec.structure_gate import check_structure, declared_paths


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
