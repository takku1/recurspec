import json
from pathlib import Path

import pytest

from recurspec.cli import main
from recurspec.project_status import StatusInstrumentError, inspect_project

FIXTURES = Path(__file__).parent / "fixtures" / "contracts"
REPO_ROOT = Path(__file__).resolve().parents[1]


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_status_reports_missing_when_there_is_no_system_md(tmp_path: Path):
    status = inspect_project(tmp_path)

    assert status.tree == "missing"
    assert status.route == "design"
    assert status.system_md == 0
    assert status.roadmap is False
    assert "No Contract Tree" in status.next_action
    assert "create ROADMAP.md" in status.next_action


def test_status_treats_unmarked_system_md_as_not_recurspec(tmp_path: Path):
    _write(
        tmp_path / "docs" / "architecture" / "SYSTEM.md",
        "# Locus — System Architecture (L0)\n\n## 1. Intent\n\nCrate map, not a contract.\n",
    )
    _write(tmp_path / "docs" / "open-work.md", "# Open Work\n")

    status = inspect_project(tmp_path)

    assert status.tree == "not_recurspec"
    assert status.route == "design"
    assert status.versioned == 0
    assert status.unversioned == ("docs/architecture/SYSTEM.md",)
    assert status.rival_registries == ("docs/open-work.md",)
    assert "source material" in status.next_action
    assert "do not stamp the version marker" in status.next_action
    assert "Create ROADMAP.md" in status.next_action
    assert "docs/open-work.md" in status.next_action


def test_status_mixed_tree_stays_not_recurspec(tmp_path: Path):
    valid = (FIXTURES / "valid" / "SYSTEM.md").read_text(encoding="utf-8")
    _write(tmp_path / "docs" / "architecture" / "SYSTEM.md", valid)
    _write(
        tmp_path / "docs" / "architecture" / "legacy" / "SYSTEM.md",
        "# Legacy notes\n\nNo Recurspec marker.\n",
    )

    status = inspect_project(tmp_path)

    assert status.tree == "not_recurspec"
    assert status.versioned == 1
    assert status.unversioned == ("docs/architecture/legacy/SYSTEM.md",)


def test_status_reports_invalid_versioned_tree(tmp_path: Path):
    text = (FIXTURES / "invalid-invariant" / "SYSTEM.md").read_text(encoding="utf-8")
    _write(tmp_path / "docs" / "architecture" / "SYSTEM.md", text)

    status = inspect_project(tmp_path)

    assert status.tree == "invalid"
    assert status.route == "repair"
    assert status.diagnostics
    assert "contract check" in status.next_action


def test_status_repairs_when_a_declared_probe_is_missing(tmp_path: Path):
    valid = (FIXTURES / "valid" / "SYSTEM.md").read_text(encoding="utf-8")
    valid = valid.replace(
        "- **Primary Metric:** valid fixture acceptance rate.",
        "- **Primary Metric:** valid fixture acceptance rate.\n"
        "- **Evaluation Gate:** `modules/ghost/measure.sh`",
    )
    _write(tmp_path / "docs" / "architecture" / "SYSTEM.md", valid)
    _write(tmp_path / "ROADMAP.md", "# Roadmap\n")

    status = inspect_project(tmp_path)

    assert status.tree == "valid"
    assert status.route == "repair"
    assert status.missing_probes == ("modules/ghost/measure.sh",)
    assert "modules/ghost/measure.sh" in status.next_action


def test_status_repairs_when_a_declared_probe_escapes_the_repository(tmp_path: Path):
    valid = (FIXTURES / "valid" / "SYSTEM.md").read_text(encoding="utf-8")
    valid = valid.replace(
        "- **Primary Metric:** valid fixture acceptance rate.",
        "- **Primary Metric:** valid fixture acceptance rate.\n"
        "- **Evaluation Gate:** `../evil.sh`",
    )
    _write(tmp_path / "docs" / "architecture" / "SYSTEM.md", valid)
    _write(tmp_path / "ROADMAP.md", "# Roadmap\n")

    status = inspect_project(tmp_path)

    assert status.tree == "valid"
    assert status.route == "repair"
    assert "../evil.sh" in status.missing_probes


def test_status_classifies_an_extra_contracts_tree(tmp_path: Path):
    valid = (FIXTURES / "valid" / "SYSTEM.md").read_text(encoding="utf-8")
    _write(tmp_path / "docs" / "architecture" / "SYSTEM.md", valid)
    _write(tmp_path / "ROADMAP.md", "# Roadmap\n")
    _write(
        tmp_path / ".recurspec" / "contracts" / "SYSTEM.md",
        "# Notes\n\nNo Recurspec marker.\n",
    )

    status = inspect_project(tmp_path)

    assert status.tree == "valid"
    assert status.route == "repair"
    assert len(status.extra_trees) == 1
    extra = status.extra_trees[0]
    assert extra.root == ".recurspec/contracts"
    assert extra.tree == "not_recurspec"
    assert extra.system_md == 1
    assert ".recurspec/contracts" in status.next_action


def test_status_reports_valid_tree_and_ready_route(tmp_path: Path):
    source = FIXTURES / "valid-tree"
    destination = tmp_path / "docs" / "architecture"
    for path in source.rglob("SYSTEM.md"):
        _write(destination / path.relative_to(source), path.read_text(encoding="utf-8"))
    _write(tmp_path / "ROADMAP.md", "# Roadmap\n")
    (tmp_path / ".recurspec").mkdir()
    (tmp_path / ".recurspec" / "worker-authorizations.json").write_text("{}", encoding="utf-8")

    status = inspect_project(tmp_path)

    assert status.tree == "valid"
    assert status.route == "ready"
    assert status.roadmap is True
    assert status.recurspec_dir is True
    assert status.checker is True
    assert status.unversioned == ()
    assert "Maker and checker must differ" in status.next_action
    assert "Keep process debt in ROADMAP.md" in status.next_action


def test_status_refuses_a_contract_root_that_escapes_the_repository(tmp_path: Path):
    with pytest.raises(StatusInstrumentError, match="escapes"):
        inspect_project(tmp_path, contract_root="..")


def test_status_cli_emits_stable_json_and_inspects_missing_repos(
    tmp_path: Path, capsys
):
    assert main(["status", str(tmp_path), "--format", "json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["tree"] == "missing"
    assert payload["route"] == "design"
    assert payload["roadmap"] is False
    assert payload["checker"] == "missing"

    assert main(["status", str(tmp_path / "absent")]) == 2
    assert "does not exist" in capsys.readouterr().err


def test_status_cli_text_lists_unversioned_and_rival_paths(tmp_path: Path, capsys):
    _write(tmp_path / "docs" / "architecture" / "SYSTEM.md", "# Notes\n")
    _write(tmp_path / "FEATURE_GAPS.md", "# Gaps\n")

    assert main(["status", str(tmp_path)]) == 0
    output = capsys.readouterr().out
    assert "tree: not_recurspec" in output
    assert "route: design" in output
    assert "docs/architecture/SYSTEM.md" in output
    assert "FEATURE_GAPS.md" in output
    assert "next:" in output


def test_this_repository_is_a_valid_recurspec_tree():
    status = inspect_project(REPO_ROOT)
    assert status.tree == "valid"
    assert status.route == "ready"
    assert status.roadmap is True
    assert status.rival_registries == ()
