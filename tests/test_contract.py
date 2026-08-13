import shutil
from importlib.resources import files
from pathlib import Path

from recurspec.contract import validate_contract

FIXTURES = Path(__file__).parent / "fixtures" / "contracts"


def _tree_variant(tmp_path: Path, replacements: dict[str, tuple[str, str]]) -> Path:
    tree = tmp_path / "tree"
    shutil.copytree(FIXTURES / "valid-tree", tree)
    for relative, (old, new) in replacements.items():
        contract_path = tree / relative
        contract_path.write_text(
            contract_path.read_text(encoding="utf-8").replace(old, new), encoding="utf-8"
        )
    return tree


def test_validate_contract_accepts_a_complete_versioned_atomic_leaf():
    result = validate_contract(FIXTURES / "valid" / "SYSTEM.md")

    assert result.valid
    assert result.diagnostics == ()
    assert len(result.contracts) == 1
    assert result.contracts[0]["contract_version"] == "1.0"
    assert result.contracts[0]["atomic_leaf"] is True


def test_validate_contract_accepts_an_independently_authored_two_stage_tree():
    result = validate_contract(FIXTURES / "valid-tree")

    assert result.valid
    assert result.diagnostics == ()
    assert len(result.contracts) == 3
    assert result.contracts[0]["inputs"] == ["source"]
    assert result.contracts[0]["outputs"] == ["artifact"]
    assert result.contracts[0]["children"] == [
        "publish/SYSTEM.md",
        "transform/SYSTEM.md",
    ]


def test_validate_contract_rejects_a_missing_child_link(tmp_path: Path):
    tree = _tree_variant(
        tmp_path,
        {"SYSTEM.md": ("publish/SYSTEM.md", "missing/SYSTEM.md")},
    )

    result = validate_contract(tree)

    actual = [(item.rule_code, Path(item.path).name, item.message) for item in result.diagnostics]
    assert actual == [
        (
            "contract.child.missing",
            "SYSTEM.md",
            "child link 'missing/SYSTEM.md' does not resolve to a Contract Node",
        ),
        (
            "contract.interface.output.unsatisfied",
            "SYSTEM.md",
            "parent output 'artifact' is unavailable after child composition",
        ),
    ]


def test_validate_contract_rejects_a_child_link_outside_the_checked_tree(tmp_path: Path):
    tree = _tree_variant(
        tmp_path,
        {"SYSTEM.md": ("publish/SYSTEM.md", "../outside/SYSTEM.md")},
    )
    shutil.copytree(tree / "publish", tmp_path / "outside")

    result = validate_contract(tree)

    assert result.diagnostics[0].rule_code == "contract.child.outside-tree"
    assert result.diagnostics[0].path == (tree / "SYSTEM.md").resolve().as_posix()


def test_validate_contract_rejects_duplicate_child_links(tmp_path: Path):
    tree = _tree_variant(
        tmp_path,
        {"SYSTEM.md": ("publish/SYSTEM.md", "./transform/SYSTEM.md")},
    )

    result = validate_contract(tree)

    assert [item.rule_code for item in result.diagnostics] == [
        "contract.child.duplicate",
        "contract.interface.output.unsatisfied",
    ]


def test_validate_contract_rejects_a_child_at_the_wrong_level(tmp_path: Path):
    tree = _tree_variant(
        tmp_path,
        {"publish/SYSTEM.md": ("# Publish (L2)", "# Publish (L3)")},
    )

    result = validate_contract(tree)

    level_diagnostic = next(
        item for item in result.diagnostics if item.rule_code == "contract.child.level"
    )
    assert level_diagnostic.path == (tree / "publish" / "SYSTEM.md").resolve().as_posix()
    assert level_diagnostic.message == "child level 3 must equal parent level 1 plus one"


def test_validate_contract_reports_each_input_without_an_available_producer(tmp_path: Path):
    tree = _tree_variant(
        tmp_path,
        {"transform/SYSTEM.md": ("**Inputs:** `source`", "**Inputs:** `upstream`")},
    )

    result = validate_contract(tree)

    assert [
        (Path(item.path).parent.name, item.rule_code, item.message)
        for item in result.diagnostics
        if item.rule_code == "contract.interface.input.unsatisfied"
    ] == [
        (
            "publish",
            "contract.interface.input.unsatisfied",
            "child input 'transformed' is unavailable during composition",
        ),
        (
            "transform",
            "contract.interface.input.unsatisfied",
            "child input 'upstream' is unavailable during composition",
        ),
    ]


def test_validate_contract_rejects_an_interface_dependency_cycle(tmp_path: Path):
    tree = _tree_variant(
        tmp_path,
        {"transform/SYSTEM.md": ("**Inputs:** `source`", "**Inputs:** `artifact`")},
    )

    result = validate_contract(tree)

    assert [item.rule_code for item in result.diagnostics] == [
        "contract.interface.output.unsatisfied",
        "contract.interface.input.unsatisfied",
        "contract.interface.input.unsatisfied",
    ]


def test_validate_contract_file_check_does_not_claim_tree_composition():
    result = validate_contract(FIXTURES / "valid-tree" / "SYSTEM.md")

    assert result.valid
    assert result.diagnostics == ()


def test_validate_contract_reports_explicit_stable_migration_diagnostics():
    result = validate_contract(FIXTURES)

    assert not result.valid
    assert [diagnostic.rule_code for diagnostic in result.diagnostics] == [
        "contract.heading.missing",
        "contract.invariant.ears",
        "contract.invariant.evidence-stage",
        "contract.version.missing",
    ]
    assert "section 8" in result.diagnostics[0].message
    assert "EARS" in result.diagnostics[1].message
    assert "Evidence Stage" in result.diagnostics[2].message
    assert "recurspec-contract: 1.0" in result.diagnostics[3].message


def test_contract_schema_is_a_bundled_package_resource():
    schema = files("recurspec").joinpath("schemas/contract-node-1.0.schema.json")

    assert schema.is_file()
    assert '"https://json-schema.org/draft/2020-12/schema"' in schema.read_text(encoding="utf-8")


def test_validate_contract_rejects_a_directory_without_contract_nodes(tmp_path: Path):
    result = validate_contract(tmp_path)

    assert not result.valid
    assert result.contracts == ()
    assert [(diagnostic.rule_code, diagnostic.message) for diagnostic in result.diagnostics] == [
        ("contract.discovery.empty", "directory contains no recursively discovered SYSTEM.md files")
    ]


def test_validate_contract_accepts_wrapped_invariants_from_the_contract_engine_spec():
    result = validate_contract(Path("docs/architecture/contract-engine/SYSTEM.md"))

    assert result.valid
    assert result.diagnostics == ()
    assert result.contracts[0]["invariants"][0] == {
        "ears_pattern": "Ubiquitous",
        "statement": (
            "The Contract Engine SHALL validate normalized Contract Nodes against "
            "JSON Schema Draft 2020-12."
        ),
        "evidence_stage": "Sampled",
    }
    assert len(result.contracts[0]["invariants"]) == 8
