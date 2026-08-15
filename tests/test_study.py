from pathlib import Path

from recurspec.cli import main
from recurspec.study import assign_pair, init_pair, is_recurspec_repository


def test_is_recurspec_repository_detects_this_package():
    assert is_recurspec_repository(Path(__file__).resolve().parents[1]) is True


def test_study_init_refuses_recurspec_as_the_subject(tmp_path: Path, capsys):
    code = main(
        [
            "study",
            "init",
            "bad",
            "--project",
            str(Path(__file__).resolve().parents[1]),
            "--task-a",
            "A",
            "--task-b",
            "B",
            "--hours",
            "4h",
            "--baseline",
            "ad-hoc",
            "--repository",
            str(tmp_path),
        ]
    )

    assert code == 1
    assert "excluded" in capsys.readouterr().err
    assert not (tmp_path / "docs" / "research" / "pairs" / "bad.md").exists()


def test_study_init_and_assign_records_a_coin_flip(tmp_path: Path):
    subject = tmp_path / "other"
    subject.mkdir()
    (subject / "pyproject.toml").write_text('name = "other"\n', encoding="utf-8")
    log = init_pair(
        tmp_path,
        pair_id="locus-01",
        project=str(subject),
        task_a="Task A",
        task_b="Task B",
        hours="4h",
        baseline="existing open-work tickets",
    )
    text = log.read_text(encoding="utf-8")
    assert "unknown" in text
    assert "unassigned" in text

    result = assign_pair(log)
    assert "Recurspec arm =" in result
    assigned = log.read_text(encoding="utf-8")
    assert "| Recurspec |" in assigned
    assert "| Baseline |" in assigned
    assert "unassigned" not in assigned

    try:
        assign_pair(log)
    except Exception as exc:
        assert "already assigned" in str(exc)
    else:
        raise AssertionError("expected refuse re-flip")


def test_study_list_cli(tmp_path: Path, capsys):
    subject = tmp_path / "other"
    subject.mkdir()
    init_pair(
        tmp_path,
        pair_id="gg-01",
        project=str(subject),
        task_a="A",
        task_b="B",
        hours="2h",
        baseline="tickets",
    )
    assert main(["study", "list", str(tmp_path)]) == 0
    output = capsys.readouterr().out
    assert "gg-01" in output
    assert "unassigned" in output
