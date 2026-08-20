import json
from pathlib import Path

import pytest

from recurspec.evidence import (
    _CORPUS_KEEP,
    export_decision_corpus,
    log_event,
)


def test_export_refuses_without_opt_in(tmp_path: Path):
    with pytest.raises(ValueError, match="opt-in"):
        export_decision_corpus(tmp_path / "evidence", tmp_path / "out.jsonl", opt_in=False)


def test_export_drops_reasons_branches_and_metric_values(tmp_path: Path):
    log_dir = tmp_path / "evidence"
    log_event(
        "contract-engine",
        "negative_pattern",
        {"secret_metric": 42, "prompt": "do not leak"},
        reason="see src/secret.py",
        branch="candidate/private",
        verdict="REVERT",
        log_dir=str(log_dir),
    )

    dest = tmp_path / "corpus.jsonl"
    count = export_decision_corpus(log_dir, dest, opt_in=True)

    assert count == 1
    row = json.loads(dest.read_text(encoding="utf-8"))
    assert row["verdict"] == "REVERT"
    assert row["event_type"] == "negative_pattern"
    assert row["metrics_present"] is True
    assert "metrics" not in row
    assert "reason" not in row
    assert "branch" not in row
    assert "secret.py" not in dest.read_text(encoding="utf-8")
    assert "candidate/private" not in dest.read_text(encoding="utf-8")


def test_decision_corpus_never_carries_a_decision_class_or_reason():
    """The redaction is the guarantee. A CLI verb whose only behavior was to refuse
    encoded the same fact as public surface area; ROADMAP R-502 records the block
    (R-701)."""
    assert "decision_class" not in _CORPUS_KEEP
    assert "reason" not in _CORPUS_KEEP
    assert "metrics" not in _CORPUS_KEEP
