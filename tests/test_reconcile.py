from pathlib import Path

import pytest

from recurspec.contract import validate_contract
from recurspec.reconcile import ReconciliationInstrumentError, plan_reconciliation


def _roots(root: Path) -> tuple[Path, Path, Path]:
    source = root / "src" / "recurspec"
    tests = root / "tests"
    contracts = root / "docs" / "architecture"
    source.mkdir(parents=True)
    tests.mkdir()
    contracts.mkdir(parents=True)
    return source, tests, contracts


def test_reconciler_turns_uncontracted_source_into_an_unknown_draft_without_writing(
    tmp_path: Path,
):
    source, _, _ = _roots(tmp_path)
    orphan = source / "new_adapter.py"
    orphan.write_text("def connect():\n    return 'unknown'\n", encoding="utf-8")

    plan = plan_reconciliation(tmp_path)

    assert len(plan.actions) == 1
    action = plan.actions[0]
    assert action.kind == "draft_leaf"
    assert action.source_path == "src/recurspec/new_adapter.py"
    assert action.contract_path == "docs/architecture/drafts/new-adapter/SYSTEM.md"
    assert "EvidenceStage:` Unknown" in action.draft_content
    assert "product behavior is deliberately unspecified" in action.draft_content
    assert "Decision class" not in action.draft_content
    assert "connect" not in action.draft_content
    assert not (tmp_path / action.contract_path).exists()
    draft = tmp_path / "draft" / "SYSTEM.md"
    draft.parent.mkdir()
    draft.write_text(action.draft_content, encoding="utf-8")
    assert validate_contract(draft).valid


def test_reconciler_proposes_review_for_bloat_and_uncontracted_test_seams(tmp_path: Path):
    source, tests, contracts = _roots(tmp_path)
    implementation = source / "feature.py"
    implementation.write_text("def feature():\n    pass\n", encoding="utf-8")
    declared_test = tests / "test_feature.py"
    declared_test.write_text("def test_feature():\n    pass\n", encoding="utf-8")
    extra_test = tests / "test_adapter.py"
    extra_test.write_text("def test_adapter():\n    pass\n", encoding="utf-8")
    contract = contracts / "feature" / "SYSTEM.md"
    contract.parent.mkdir()
    contract.write_text(
        "# Feature\n\n## 6. Leaf Execution & Test Seam\n\n"
        "- **Implementation:** `src/recurspec/feature.py`.\n"
        "- **Tests:** `tests/test_feature.py`.\n\n"
        "## 7. Measurement Seams\n"
        + "\n".join(f"line {number}" for number in range(151)),
        encoding="utf-8",
    )

    plan = plan_reconciliation(tmp_path, bloat_line_limit=150)

    assert [(action.kind, action.source_path) for action in plan.actions] == [
        ("split_review", "docs/architecture/feature/SYSTEM.md"),
        ("test_seam_review", "tests/test_adapter.py"),
    ]


def test_reconciler_defers_metric_only_feedback_to_the_evaluation_gate(tmp_path: Path):
    _roots(tmp_path)

    plan = plan_reconciliation(tmp_path, evidence_events=[{"event_type": "signal_d"}])

    assert plan.actions == ()
    assert plan.deferred_empirical_events == 1


def test_reconciler_refuses_to_draft_from_a_broken_structure_instrument(tmp_path: Path):
    source, _, _ = _roots(tmp_path)
    (source / "broken.py").write_text("def broken(:\n", encoding="utf-8")

    with pytest.raises(ReconciliationInstrumentError, match="structure instrument"):
        plan_reconciliation(tmp_path)


def test_reconciler_proposes_split_for_four_explicit_separable_responsibilities(tmp_path: Path):
    _, _, contracts = _roots(tmp_path)
    contract = contracts / "feature" / "SYSTEM.md"
    contract.parent.mkdir()
    contract.write_text(
        "# Feature\n\n## 1. System Intent & Responsibility\n\n"
        "- **Responsibilities:** Parse; Store; Publish; Audit\n\n"
        "## 6. Leaf Execution & Test Seam\n\n## 7. Measurement Seams\n",
        encoding="utf-8",
    )

    plan = plan_reconciliation(tmp_path)

    assert plan.actions[0].kind == "split_review"
    assert "4 separable responsibilities" in plan.actions[0].reason
