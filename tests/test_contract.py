import shutil
from importlib.resources import files
from pathlib import Path

import pytest

from recurspec.cli import main
from recurspec.contract import (
    ContractInstrumentError,
    audit_evidence_stages,
    build_tree_index,
    decision_class,
    resolve_child_path,
    validate_contract,
)

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


def test_decision_class_extracts_the_section_eight_decision():
    result = validate_contract(FIXTURES / "valid" / "SYSTEM.md")

    assert decision_class(result.contracts[0]["sections"]) == "BUILD"


def test_decision_class_is_none_without_a_section_eight():
    result = validate_contract(FIXTURES / "valid-tree" / "SYSTEM.md")

    assert decision_class(result.contracts[0]["sections"]) is None


def test_resolve_child_path_expands_a_directory_link_to_its_system_md(tmp_path: Path):
    parent = tmp_path / "root" / "SYSTEM.md"
    (tmp_path / "root" / "child").mkdir(parents=True)

    resolved = resolve_child_path(parent, "./child")

    assert resolved == (tmp_path / "root" / "child" / "SYSTEM.md").resolve()


def test_build_tree_index_maps_node_id_to_parent_id():
    index = build_tree_index(FIXTURES / "valid-tree")

    assert index["SYSTEM.md"]["parent_id"] is None
    assert index["transform/SYSTEM.md"]["parent_id"] == "SYSTEM.md"
    assert index["publish/SYSTEM.md"]["parent_id"] == "SYSTEM.md"
    assert set(index) == {"SYSTEM.md", "transform/SYSTEM.md", "publish/SYSTEM.md"}


def test_build_tree_index_resolves_parent_ids_from_a_relative_tree_root(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    """A relative tree_root must index identically to its absolute form: paths built
    from an un-resolved rglob() never matched resolve_child_path()'s always-resolved
    output, so every non-root node's parent_id silently came back None instead of the
    real parent."""
    tree = tmp_path / "tree"
    shutil.copytree(FIXTURES / "valid-tree", tree)
    monkeypatch.chdir(tmp_path)

    index = build_tree_index("tree")

    assert index["transform/SYSTEM.md"]["parent_id"] == "SYSTEM.md"
    assert index["publish/SYSTEM.md"]["parent_id"] == "SYSTEM.md"


def test_build_tree_index_refuses_an_invalid_tree(tmp_path: Path):
    (tmp_path / "SYSTEM.md").write_text("# Broken (L0)\nno contract marker\n", encoding="utf-8")

    with pytest.raises(ContractInstrumentError):
        build_tree_index(tmp_path)


def test_validate_contract_recognizes_a_bold_annotated_atomic_leaf_declaration(
    tmp_path: Path,
):
    contract_path = tmp_path / "SYSTEM.md"
    contract_path.write_text(
        (FIXTURES / "valid" / "SYSTEM.md")
        .read_text(encoding="utf-8")
        .replace("Atomic leaf.", "**Atomic leaf (procured).**"),
        encoding="utf-8",
    )

    result = validate_contract(contract_path)

    assert result.valid, result.diagnostics
    assert result.contracts[0]["atomic_leaf"] is True


def test_validate_contract_accepts_a_complete_versioned_atomic_leaf():
    result = validate_contract(FIXTURES / "valid" / "SYSTEM.md")

    assert result.valid
    assert result.diagnostics == ()
    assert len(result.contracts) == 1
    assert result.contracts[0]["contract_version"] == "1.0"
    assert result.contracts[0]["atomic_leaf"] is True


def test_validate_contract_rejects_an_atomic_leaf_missing_execution_sections():
    result = validate_contract(FIXTURES / "invalid-atomic-leaf")

    assert not result.valid
    assert any(
        diagnostic.rule_code == "contract.heading.missing"
        and "section 8" in diagnostic.message
        for diagnostic in result.diagnostics
    )


def test_contract_diagnostics_are_stable_across_repeated_validation():
    contract = FIXTURES / "invalid-invariant"

    first = validate_contract(contract).diagnostics
    second = validate_contract(contract).diagnostics

    assert first == second


def test_validate_contract_recognizes_a_genuinely_combined_complex_ears_pattern():
    result = validate_contract(FIXTURES / "valid" / "SYSTEM.md")

    assert result.valid
    complex_invariants = [
        invariant
        for invariant in result.contracts[0]["invariants"]
        if invariant["ears_pattern"] == "Complex"
    ]
    assert complex_invariants == [
        {
            "ears_pattern": "Complex",
            "statement": (
                "WHILE a directory scan is active, WHEN a malformed file is found THE "
                "SYSTEM SHALL record a diagnostic and continue scanning."
            ),
            "evidence_stage": "Sampled",
        }
    ]


def test_validate_contract_rejects_complex_tagged_on_a_single_keyword_statement(
    tmp_path: Path,
):
    contract_path = tmp_path / "SYSTEM.md"
    contract_path.write_text(
        (FIXTURES / "valid" / "SYSTEM.md")
        .read_text(encoding="utf-8")
        .replace(
            "WHILE a directory scan is active, WHEN a malformed file is found THE SYSTEM "
            "SHALL record a diagnostic and continue scanning.",
            "WHILE a directory scan is active THE SYSTEM SHALL record a diagnostic.",
        ),
        encoding="utf-8",
    )

    result = validate_contract(contract_path)

    assert not result.valid
    assert any(
        diagnostic.rule_code == "contract.invariant.ears" for diagnostic in result.diagnostics
    )


def test_validate_contract_recognizes_the_optional_feature_ears_pattern():
    result = validate_contract(FIXTURES / "valid" / "SYSTEM.md")

    assert result.valid
    optional_invariants = [
        invariant
        for invariant in result.contracts[0]["invariants"]
        if invariant["ears_pattern"] == "Optional"
    ]
    assert optional_invariants == [
        {
            "ears_pattern": "Optional",
            "statement": (
                "WHERE the `--format json` flag is given THE SYSTEM SHALL emit a stable "
                "machine-readable payload."
            ),
            "evidence_stage": "Sampled",
        }
    ]


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


def test_validate_contract_ignores_an_external_link_in_section_two(tmp_path: Path):
    """A plain URL citation in section 2 (e.g. an upstream RFC) is not a declared
    child - it must not be resolved as a repository-relative path and flagged
    'outside the checked tree'."""
    tree = _tree_variant(
        tmp_path,
        {
            "SYSTEM.md": (
                "- [Transform](transform/SYSTEM.md)",
                "- [Transform](transform/SYSTEM.md)\n"
                "- [External spec](https://example.com/spec)",
            )
        },
    )

    result = validate_contract(tree)

    assert result.valid
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
    root_count_message = (
        "expected exactly one Contract Tree root; found 2 unreferenced candidate(s): "
        "SYSTEM.md, publish/SYSTEM.md"
    )
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
        # publish/SYSTEM.md was orphaned by redirecting the only link that reached it;
        # it and the real root both now show zero incoming links (R-603).
        ("contract.tree.root_count", "SYSTEM.md", root_count_message),
        ("contract.tree.root_count", "SYSTEM.md", root_count_message),
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

    # publish/SYSTEM.md is orphaned once both link slots point at transform (R-603).
    assert [item.rule_code for item in result.diagnostics] == [
        "contract.child.duplicate",
        "contract.interface.output.unsatisfied",
        "contract.tree.root_count",
        "contract.tree.root_count",
    ]


def test_validate_contract_flags_a_duplicate_section_heading(tmp_path: Path):
    """A duplicate '## 1.' heading must be reported, not silently overwrite the
    first occurrence's content with no diagnostic."""
    tree = _tree_variant(
        tmp_path,
        {
            "SYSTEM.md": (
                "## 2. Sub-System Decomposition",
                "## 1. Duplicate Intent\n\nStray duplicate heading text.\n\n"
                "## 2. Sub-System Decomposition",
            )
        },
    )

    result = validate_contract(tree / "SYSTEM.md")

    assert "contract.heading.duplicate" in {item.rule_code for item in result.diagnostics}


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
    # FIXTURES bundles several independent, unrelated fixture subtrees in one directory
    # (not a single real Contract Tree), so this only checks that each fixture's own
    # intended defect still fires - not the full diagnostic set, which now also gains
    # R-603 tree-shape diagnostics (multiple unreferenced roots) from that same
    # unrelatedness. See test_validate_contract_accepts_an_independently_authored_...
    # and the R-603 tests below for the tree-shape checks themselves.
    result = validate_contract(FIXTURES)

    assert not result.valid
    by_code = {diagnostic.rule_code: diagnostic for diagnostic in result.diagnostics}
    assert "section 8" in by_code["contract.heading.missing"].message
    assert "EARS" in by_code["contract.invariant.ears"].message
    assert "Evidence Stage" in by_code["contract.invariant.evidence-stage"].message
    assert "recurspec-contract: 1.0" in by_code["contract.version.missing"].message


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
                "JSON Schema Draft 2020-12. "
                "(`test_validate_contract_accepts_a_complete_versioned_atomic_leaf`)"
            ),
        "evidence_stage": "Sampled",
    }
    assert len(result.contracts[0]["invariants"]) == 9
    assert result.contracts[0]["invariants"][-1]["ears_pattern"] == "Event-driven"
    assert "test_evidence_audit_lists_unlicensed_sampled_and_counts_unknown" in (
        result.contracts[0]["invariants"][-1]["statement"]
    )


def test_recurspecs_own_architecture_tree_passes_its_own_contract_engine():
    result = validate_contract(Path("docs/architecture"))

    assert result.valid, result.diagnostics
    assert len(result.contracts) == 11


def test_log_archive_example_tree_is_a_valid_contract_tree():
    result = validate_contract(Path("docs/examples/log-archive"))

    assert result.valid, result.diagnostics
    assert len(result.contracts) == 3


# --- R-603: hollow and disconnected Contract Trees -------------------------


_HOLLOW_PLACEHOLDER = """# Placeholder (L1)

<!-- recurspec-contract: 1.0 -->

## 1. System Intent & Responsibility

Placeholder awaiting decomposition.

## 2. Sub-System Decomposition

Decomposition pending.

## 3. Interface Contracts

- **Inputs:** none.
- **Outputs:** none.

## 4. Invariants (EARS + Epistemic Stage)

- **[Ubiquitous]** THE SYSTEM SHALL exist.
  - `EvidenceStage:` Unknown

## 5. Architectural Decisions (ADRs)

- **ADR-001:** none yet.
"""


def test_validate_contract_rejects_a_hollow_non_leaf_node(tmp_path: Path):
    contract_path = tmp_path / "SYSTEM.md"
    contract_path.write_text(_HOLLOW_PLACEHOLDER, encoding="utf-8")

    result = validate_contract(contract_path)

    assert not result.valid
    assert any(item.rule_code == "contract.node.hollow" for item in result.diagnostics)


def test_build_tree_index_refuses_a_hollow_non_leaf_node(tmp_path: Path):
    (tmp_path / "SYSTEM.md").write_text(_HOLLOW_PLACEHOLDER, encoding="utf-8")

    with pytest.raises(ContractInstrumentError):
        build_tree_index(tmp_path)


def test_validate_contract_rejects_a_valid_but_unlinked_node_in_the_tree(tmp_path: Path):
    tree = tmp_path / "tree"
    shutil.copytree(FIXTURES / "valid-tree", tree)
    orphan = tree / "orphan"
    orphan.mkdir()
    (orphan / "SYSTEM.md").write_text(
        (FIXTURES / "valid" / "SYSTEM.md")
        .read_text(encoding="utf-8")
        .replace("(L2)", "(L1)"),
        encoding="utf-8",
    )

    result = validate_contract(tree)

    # An unlinked node is indistinguishable from a second root candidate without more
    # context, so it is flagged via contract.tree.root_count rather than a separate
    # "unreachable" code - either way the tree must no longer validate (R-603).
    assert not result.valid
    assert any(
        item.rule_code == "contract.tree.root_count" and Path(item.path).parent.name == "orphan"
        for item in result.diagnostics
    )

    with pytest.raises(ContractInstrumentError):
        build_tree_index(tree)


def test_validate_contract_rejects_a_disconnected_cycle_even_with_a_single_root(
    tmp_path: Path,
):
    # A mutually-referencing island (each side has in-degree 1) has no extra root
    # candidate by in-degree alone, so this exercises the separate BFS-reachability
    # check rather than contract.tree.root_count.
    tree = tmp_path / "tree"
    tree.mkdir()

    def write(relative: str, level: int, children: str = "", atomic: bool = False) -> None:
        path = tree / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        decomposition = "Atomic leaf." if atomic else children
        path.write_text(
            f"""# Node {relative} (L{level})

<!-- recurspec-contract: 1.0 -->

## 1. System Intent & Responsibility

Fixture node.

## 2. Sub-System Decomposition

{decomposition}

## 3. Interface Contracts

- **Inputs:** none.
- **Outputs:** none.

## 4. Invariants (EARS + Epistemic Stage)

- **[Ubiquitous]** THE SYSTEM SHALL exist.
  - `EvidenceStage:` Unknown

## 5. Architectural Decisions (ADRs)

- **ADR-001:** none yet.
""",
            encoding="utf-8",
        )

    write("SYSTEM.md", 0, children="- [Leaf](./leaf/SYSTEM.md)")
    write("leaf/SYSTEM.md", 1, atomic=True)
    write("island-a/SYSTEM.md", 1, children="- [B](../island-b/SYSTEM.md)")
    write("island-b/SYSTEM.md", 1, children="- [A](../island-a/SYSTEM.md)")

    result = validate_contract(tree)

    unreachable = {Path(item.path).parent.name for item in result.diagnostics
                   if item.rule_code == "contract.node.unreachable"}
    assert unreachable == {"island-a", "island-b"}

    with pytest.raises(ContractInstrumentError):
        build_tree_index(tree)


def test_validate_contract_rejects_a_node_linked_from_two_parents(tmp_path: Path):
    tree = tmp_path / "tree"
    tree.mkdir()

    def write(relative: str, level: int, children: str = "", atomic: bool = False) -> None:
        path = tree / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        decomposition = "Atomic leaf." if atomic else children
        path.write_text(
            f"""# Node {relative} (L{level})

<!-- recurspec-contract: 1.0 -->

## 1. System Intent & Responsibility

Fixture node.

## 2. Sub-System Decomposition

{decomposition}

## 3. Interface Contracts

- **Inputs:** none.
- **Outputs:** none.

## 4. Invariants (EARS + Epistemic Stage)

- **[Ubiquitous]** THE SYSTEM SHALL exist.
  - `EvidenceStage:` Unknown

## 5. Architectural Decisions (ADRs)

- **ADR-001:** none yet.
""",
            encoding="utf-8",
        )

    write("SYSTEM.md", 0, children="- [A](./branch-a/SYSTEM.md)\n- [B](./branch-b/SYSTEM.md)")
    write("branch-a/SYSTEM.md", 1, children="- [Shared](../shared/SYSTEM.md)")
    write("branch-b/SYSTEM.md", 1, children="- [Shared](../shared/SYSTEM.md)")
    write("shared/SYSTEM.md", 2, atomic=True)

    result = validate_contract(tree)

    multi_parent = [
        item for item in result.diagnostics if item.rule_code == "contract.child.multiple_parents"
    ]
    assert len(multi_parent) == 1
    assert Path(multi_parent[0].path).parent.name == "shared"

    with pytest.raises(ContractInstrumentError):
        build_tree_index(tree)


def test_evidence_audit_lists_unlicensed_sampled_and_counts_unknown(tmp_path: Path):
    contract = tmp_path / "SYSTEM.md"
    contract.write_text(
        """# Evidence Audit Leaf (L2)

<!-- recurspec-contract: 1.0 -->

## 1. System Intent & Responsibility

Audit fixture.

## 2. Sub-System Decomposition

Atomic leaf.

## 3. Interface Contracts

- **Inputs:** Markdown.
- **Outputs:** Diagnostics.

## 4. Invariants (EARS + Epistemic Stage)

- **[Ubiquitous]** THE SYSTEM SHALL emit deterministic diagnostics. (`test_foo`)
  - `EvidenceStage:` Sampled
- **[Event-driven]** WHEN validation begins THE SYSTEM SHALL load the bundled schema.
  - `EvidenceStage:` Sampled
- **[State-driven]** WHILE a directory is checked THE SYSTEM SHALL inspect every Contract Node.
  - `EvidenceStage:` Unknown

## 5. Architectural Decisions (ADRs)

- **ADR-001:** Use a public validation seam.

## 6. Leaf Execution & Test Seam

- **Implementation Files:** `src/example.py`.
- **Test Surface Seam:** `tests/test_example.py`.

## 7. Measurement Seams

- **Primary Metric:** valid fixture acceptance rate.

## 8. Technology Resolution

- **Decision class:** BUILD
- **Selected:** Python.
""",
        encoding="utf-8",
    )

    audit = audit_evidence_stages(contract)

    assert audit.counts["Sampled"] == 2
    assert audit.counts["Unknown"] == 1
    assert audit.counts["Measured"] == 0
    assert len(audit.unlicensed) == 1
    assert audit.unlicensed[0].stage == "Sampled"
    assert "names no check" in audit.unlicensed[0].issue
    assert len(audit.unknowns) == 1
    assert audit.unknowns[0].stage == "Unknown"
    assert validate_contract(contract).valid


def test_contract_evidence_cli_is_observation_only(tmp_path: Path, capsys):
    import json

    source = Path("tests/fixtures/contracts/valid/SYSTEM.md")
    copy = tmp_path / "SYSTEM.md"
    copy.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")

    assert main(["contract", "evidence", str(copy), "--format", "json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["unlicensed"]
    assert payload["counts"]["Sampled"] >= 1
    assert validate_contract(copy).valid
