from pathlib import Path

import pytest

from recurspec.frontier import (
    FrontierInstrumentError,
    check_frontiers,
    github_issue_publisher,
    publish_frontiers,
)


def _defer_leaf(root: Path) -> Path:
    tree = root / "docs" / "architecture"
    tree.mkdir(parents=True)
    (tree / "SYSTEM.md").write_text(
        """# Research Leaf (L1)

<!-- recurspec-contract: 1.0 -->

## 1. System Intent & Responsibility

Hold an unresolved uncertainty.

## 2. Sub-System Decomposition

Atomic leaf.

## 3. Interface Contracts

- **Inputs:** `question`
- **Outputs:** `note`

## 4. Invariants (EARS + Epistemic Stage)

- **[Ubiquitous]** THE SYSTEM SHALL refuse to guess.
  - `EvidenceStage:` Sampled

## 5. Architectural Decisions (ADRs)

- **ADR-001:** Stay deferred until the survey completes.

## 6. Leaf Execution & Test Seam

- **Implementation Files:** not yet built.
- **Test Surface Seam:** none yet.

## 7. Measurement Seams

- **Primary Metric:** none.

## 8. Technology Resolution

- **Decision class:** DEFER
- **Selected:** none
- **Standard / protocol:** none
- **Alternatives considered:**
  | Option | Why not |
  |--------|---------|
  | Guess | Forbidden |
- **Fit gap:** survey incomplete
- **Seam:** none
- **Exit cost:** LOW
- **Cost model:** none
- **Liability transferred:** none
- **Operational owner:** us
- **Failure mode:** remain deferred
- **Open questions:** ROADMAP R-999
""",
        encoding="utf-8",
    )
    (root / "ROADMAP.md").write_text("# Roadmap\n", encoding="utf-8")
    return tree


def test_publish_writes_a_research_frontier_linked_to_the_contract(tmp_path: Path):
    tree = _defer_leaf(tmp_path)
    dest = tmp_path / "frontiers"

    report = publish_frontiers(tree, dest)

    assert len(report.written) == 1
    text = report.written[0].read_text(encoding="utf-8")
    assert "Research Frontier" in text
    assert "Type B" not in text
    assert "Wayfinder" not in text
    assert "`docs/architecture/SYSTEM.md`" in text
    check = check_frontiers(dest, tmp_path)
    assert check.integrity == 1.0
    assert check.broken == ()


def test_check_reports_a_ticket_whose_contract_is_gone(tmp_path: Path):
    dest = tmp_path / "frontiers"
    dest.mkdir()
    (dest / "orphan.md").write_text(
        "# Research Frontier: gone\n\n- **Contract:** `docs/missing/SYSTEM.md`\n",
        encoding="utf-8",
    )

    check = check_frontiers(dest, tmp_path)

    assert check.integrity == 0.0
    assert check.broken == ("orphan.md",)


def test_github_publisher_refuses_a_failed_remote_call():
    class Result:
        returncode = 1
        stderr = "auth required"
        stdout = ""

    publisher = github_issue_publisher(lambda _args: Result())

    with pytest.raises(FrontierInstrumentError, match="auth required"):
        publisher("title", "body")
