import json
from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from recurspec import check_project
from recurspec.cli import main

ROOT = Path(__file__).resolve().parents[1]


def test_check_cli_aggregates_selected_read_only_checks(tmp_path: Path, capsys):
    contract = tmp_path / "docs" / "architecture" / "SYSTEM.md"
    contract.parent.mkdir(parents=True)
    contract.write_text("# Not a Recurspec contract\n", encoding="utf-8")
    frontiers = tmp_path / ".recurspec" / "frontiers"
    frontiers.mkdir(parents=True)
    (frontiers / "orphan.md").write_text(
        "# Research Frontier\n\n- **Contract:** `docs/missing/SYSTEM.md`\n",
        encoding="utf-8",
    )
    before = {
        path.relative_to(tmp_path).as_posix(): path.read_bytes()
        for path in tmp_path.rglob("*")
        if path.is_file()
    }

    code = main(
        [
            "check",
            str(tmp_path),
            "--only",
            "contract,frontier",
            "--format",
            "json",
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    assert code == 1
    assert payload == {
        "checks": ["contract", "frontier"],
        "findings": [
            {
                "blocking": True,
                "checker": "contract",
                "code": "contract.tree.root_count",
                "details": {"path": "docs/architecture"},
                "evidence_class": "static_structure",
                "evidence_stage": "Observed",
                "message": (
                    "expected exactly one Contract Tree root; found 0 "
                    "unreferenced candidate(s): none"
                ),
            },
            {
                "blocking": True,
                "checker": "contract",
                "code": "contract.version.missing",
                "details": {"path": "docs/architecture/SYSTEM.md"},
                "evidence_class": "static_structure",
                "evidence_stage": "Observed",
                "message": "missing '<!-- recurspec-contract: 1.0 -->' metadata",
            },
            {
                "blocking": True,
                "checker": "frontier",
                "code": "frontier.contract.missing",
                "details": {"ticket": "orphan.md"},
                "evidence_class": "static_structure",
                "evidence_stage": "Observed",
                "message": "Research Frontier ticket does not point to an existing Contract Node",
            },
        ],
        "indeterminate": False,
        "valid": False,
    }
    after = {
        path.relative_to(tmp_path).as_posix(): path.read_bytes()
        for path in tmp_path.rglob("*")
        if path.is_file()
    }
    assert after == before


def test_check_cli_combines_comma_separated_and_repeated_only_values(capsys):
    code = main(
        [
            "check",
            str(ROOT),
            "--only",
            "contract,evidence",
            "--only",
            "frontier",
            "--format",
            "json",
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    assert code in {0, 1}
    assert payload["checks"] == ["contract", "evidence", "frontier"]


def test_check_cli_text_reports_nonblocking_findings_and_pass_summary(
    tmp_path: Path, capsys
):
    source = ROOT / "tests" / "fixtures" / "contracts" / "valid" / "SYSTEM.md"
    contract = tmp_path / "docs" / "architecture" / "SYSTEM.md"
    contract.parent.mkdir(parents=True)
    contract.write_text(
        source.read_text(encoding="utf-8").replace(
            "`EvidenceStage:` Sampled", "`EvidenceStage:` Unknown", 1
        ),
        encoding="utf-8",
    )

    code = main(["check", str(tmp_path), "--only", "evidence"])

    output = capsys.readouterr().out
    assert code == 0
    assert "evidence: evidence.claim.unlicensed:" in output
    assert "evidence: evidence.stage.unknown:" in output
    assert output.rstrip().endswith("PASS: 1 selected check(s) completed")


def test_check_project_preserves_evidence_licenses_in_an_immutable_report(tmp_path: Path):
    source = ROOT / "tests" / "fixtures" / "contracts" / "valid" / "SYSTEM.md"
    contract = tmp_path / "docs" / "architecture" / "SYSTEM.md"
    contract.parent.mkdir(parents=True)
    contract.write_text(
        source.read_text(encoding="utf-8").replace(
            "`EvidenceStage:` Sampled", "`EvidenceStage:` Unknown", 1
        ),
        encoding="utf-8",
    )

    report = check_project(tmp_path, checks=("evidence",))

    assert report.exit_code == 0
    assert report.valid is True
    assert len(report.findings) == 5
    assert {item.code for item in report.findings} == {
        "evidence.claim.unlicensed",
        "evidence.stage.unknown",
    }
    assert {item.evidence_stage for item in report.findings} == {"Sampled", "Unknown"}
    assert {item.evidence_class for item in report.findings} == {"static_structure"}
    assert all(item.blocking is False for item in report.findings)
    assert all(dict(item.details)["invariant_index"] >= 1 for item in report.findings)
    with pytest.raises(FrozenInstanceError):
        report.indeterminate = True
    with pytest.raises(TypeError):
        report.findings[0].details[0] = ("invariant_index", 99)


def test_check_project_runs_every_checker_and_honors_changed_files(tmp_path: Path):
    fixture = ROOT / "tests" / "fixtures" / "contracts" / "valid" / "SYSTEM.md"
    contract = tmp_path / "docs" / "architecture" / "SYSTEM.md"
    contract.parent.mkdir(parents=True)
    contract.write_text(fixture.read_text(encoding="utf-8"), encoding="utf-8")
    (tmp_path / "src" / "recurspec").mkdir(parents=True)
    (tmp_path / "src" / "recurspec" / "orphan.py").write_text(
        "def visible():\n    return True\n", encoding="utf-8"
    )
    (tmp_path / "src" / "recurspec" / "ignored.py").write_text(
        "def ignored():\n    return True\n", encoding="utf-8"
    )
    (tmp_path / "src" / "example.py").write_text("value = 1\n", encoding="utf-8")
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_example.py").write_text(
        "def test_example():\n    assert True\n", encoding="utf-8"
    )
    frontiers = tmp_path / ".recurspec" / "frontiers"
    frontiers.mkdir(parents=True)
    (frontiers / "orphan.md").write_text(
        "# Research Frontier\n\n- **Contract:** `docs/missing/SYSTEM.md`\n",
        encoding="utf-8",
    )

    report = check_project(
        tmp_path,
        changed_files={"src/recurspec/orphan.py"},
    )

    assert report.checks == (
        "contract",
        "evidence",
        "structure",
        "resolution",
        "frontier",
    )
    assert report.exit_code == 1
    assert report.indeterminate is False
    assert {item.checker for item in report.findings} == {
        "evidence",
        "structure",
        "resolution",
        "frontier",
    }
    assert any(item.code == "structure.public.uncontracted" for item in report.findings)
    assert not any(
        dict(item.details).get("path", "").endswith("ignored.py")
        for item in report.findings
    )
    assert any(item.code == "resolution.field.missing" for item in report.findings)


def test_check_project_treats_missing_instrument_input_as_indeterminate(tmp_path: Path):
    missing = tmp_path / "absent"

    report = check_project(missing, checks=("contract", "frontier"))

    assert report.exit_code == 2
    assert report.indeterminate is True
    assert report.findings[0].as_dict() == {
        "blocking": True,
        "checker": "inspection",
        "code": "inspection.repository.missing",
        "details": {"path": missing.as_posix()},
        "evidence_class": "static_structure",
        "evidence_stage": "Unknown",
        "message": "repository does not exist",
    }
    assert not missing.exists()
