from pathlib import Path

from recurspec.spec_runner.context_packer import (
    BudgetOverflow,
    Packet,
    SchemaRejected,
    contract_card,
    estimate_tokens,
    pack,
)

LEAF_TEMPLATE = """# {title} (L{level})

<!-- recurspec-contract: 1.0 -->

## 1. System Intent & Responsibility

{body_marker}

## 2. Sub-System Decomposition

Atomic leaf.

## 3. Interface Contracts

- **Inputs:** none.
- **Outputs:** none. {interface_marker}

## 4. Invariants (EARS + Epistemic Stage)

- **[Ubiquitous]** THE SYSTEM SHALL do the thing.
  - `EvidenceStage:` Sampled

## 5. Architectural Decisions (ADRs)

- **ADR-001:** n/a.

## 6. Leaf Execution & Test Seam

- **Implementation Files:** `src/example.py`.
- **Test Surface Seam:** `tests/test_example.py`.

## 7. Measurement Seams

- **Primary Metric:** n/a.

## 8. Technology Resolution

- **Decision class:** BUILD
- **Selected:** Python.
"""

NON_LEAF_TEMPLATE = """# {title} (L{level})

<!-- recurspec-contract: 1.0 -->

## 1. System Intent & Responsibility

{body_marker}

## 2. Sub-System Decomposition

{children_links}

## 3. Interface Contracts

- **Inputs:** none.
- **Outputs:** none.

## 4. Invariants (EARS + Epistemic Stage)

- **[Ubiquitous]** THE SYSTEM SHALL compose its children.
  - `EvidenceStage:` Sampled

## 5. Architectural Decisions (ADRs)

- **ADR-001:** n/a.
"""


def _build_grandparent_parent_siblings_tree(root: Path) -> None:
    """root (L0) -> mid (L1) -> {target, sibling} (L2)."""
    (root / "mid" / "target").mkdir(parents=True)
    (root / "mid" / "sibling").mkdir(parents=True)

    (root / "SYSTEM.md").write_text(
        NON_LEAF_TEMPLATE.format(
            title="Root",
            level=0,
            body_marker="GRANDPARENT_BODY_MARKER must never appear in a grandchild's packet.",
            children_links="- [mid](./mid/SYSTEM.md)",
        ),
        encoding="utf-8",
    )
    (root / "mid" / "SYSTEM.md").write_text(
        NON_LEAF_TEMPLATE.format(
            title="Mid",
            level=1,
            body_marker="PARENT_BODY_MARKER should appear in the target's packet.",
            children_links="- [target](./target/SYSTEM.md)\n- [sibling](./sibling/SYSTEM.md)",
        ),
        encoding="utf-8",
    )
    (root / "mid" / "target" / "SYSTEM.md").write_text(
        LEAF_TEMPLATE.format(
            title="Target",
            level=2,
            body_marker="TARGET_OWN_DRAFT_MARKER.",
            interface_marker="",
        ),
        encoding="utf-8",
    )
    (root / "mid" / "sibling" / "SYSTEM.md").write_text(
        LEAF_TEMPLATE.format(
            title="Sibling",
            level=2,
            body_marker="SIBLING_BODY_MARKER must never appear - siblings contribute §3 only.",
            interface_marker="SIBLING_INTERFACE_MARKER should appear in the target's packet.",
        ),
        encoding="utf-8",
    )


def test_pack_includes_parent_context_but_never_the_grandparent(tmp_path: Path):
    _build_grandparent_parent_siblings_tree(tmp_path)

    result = pack("mid/target/SYSTEM.md", tmp_path, max_tokens_per_node=100_000)

    assert isinstance(result, Packet)
    assert "PARENT_BODY_MARKER" in result.parent_context
    assert "GRANDPARENT_BODY_MARKER" not in result.parent_context
    assert "GRANDPARENT_BODY_MARKER" not in result.contract_card
    assert "GRANDPARENT_BODY_MARKER" not in result.sibling_interfaces
    assert "GRANDPARENT_BODY_MARKER" not in result.own_draft


def test_pack_includes_sibling_interfaces_but_never_sibling_bodies(tmp_path: Path):
    _build_grandparent_parent_siblings_tree(tmp_path)

    result = pack("mid/target/SYSTEM.md", tmp_path, max_tokens_per_node=100_000)

    assert isinstance(result, Packet)
    assert "SIBLING_INTERFACE_MARKER" in result.sibling_interfaces
    assert "SIBLING_BODY_MARKER" not in result.sibling_interfaces
    assert "SIBLING_BODY_MARKER" not in result.parent_context
    assert "SIBLING_BODY_MARKER" not in result.own_draft


def test_pack_refuses_with_budget_overflow_rather_than_truncate(tmp_path: Path):
    _build_grandparent_parent_siblings_tree(tmp_path)

    result = pack("mid/target/SYSTEM.md", tmp_path, max_tokens_per_node=1)

    assert isinstance(result, BudgetOverflow)
    assert result.max_tokens_per_node == 1
    assert result.estimated_tokens > 1
    assert result.largest_contributor in {
        "contract_card",
        "parent_context",
        "sibling_interfaces",
        "own_draft",
        "survey_context",
    }


def test_contract_card_is_byte_identical_across_two_different_nodes(tmp_path: Path):
    _build_grandparent_parent_siblings_tree(tmp_path)

    target_result = pack("mid/target/SYSTEM.md", tmp_path, max_tokens_per_node=100_000)
    sibling_result = pack("mid/sibling/SYSTEM.md", tmp_path, max_tokens_per_node=100_000)

    assert isinstance(target_result, Packet)
    assert isinstance(sibling_result, Packet)
    assert target_result.contract_card == sibling_result.contract_card == contract_card()


def test_pack_returns_schema_rejected_instead_of_dispatching_an_invalid_tree(tmp_path: Path):
    _build_grandparent_parent_siblings_tree(tmp_path)
    # Break the sibling: strip its version marker so the whole tree fails validation.
    sibling_path = tmp_path / "mid" / "sibling" / "SYSTEM.md"
    sibling_path.write_text(
        sibling_path.read_text(encoding="utf-8").replace(
            "<!-- recurspec-contract: 1.0 -->\n\n", ""
        ),
        encoding="utf-8",
    )

    result = pack("mid/target/SYSTEM.md", tmp_path, max_tokens_per_node=100_000)

    assert isinstance(result, SchemaRejected)
    assert result.diagnostics


def test_pack_raises_for_an_unknown_node_id(tmp_path: Path):
    _build_grandparent_parent_siblings_tree(tmp_path)

    try:
        pack("mid/does-not-exist/SYSTEM.md", tmp_path, max_tokens_per_node=100_000)
        raised = False
    except KeyError:
        raised = True
    assert raised


def test_estimate_tokens_is_conservative_and_zero_for_empty_text():
    assert estimate_tokens("") == 0
    assert estimate_tokens("abc") == 1
    assert estimate_tokens("a" * 300) == 100
