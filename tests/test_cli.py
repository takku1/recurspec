from pathlib import Path

from recurspec.cli import build_parser, sync_skill


def test_parser_exposes_the_two_public_commands():
    parser = build_parser()

    evaluate = parser.parse_args(["evaluate", "checkout", "candidate/42"])
    skills = parser.parse_args(["skills", "check", "--target", "codex"])

    assert evaluate.module == "checkout"
    assert evaluate.candidate_branch == "candidate/42"
    assert skills.action == "check"
    assert skills.target == "codex"


def test_skill_sync_installs_one_self_contained_skill(tmp_path: Path):
    assert sync_skill(tmp_path, check=True) is False
    assert sync_skill(tmp_path) is False
    assert sync_skill(tmp_path, check=True) is True

    installed = tmp_path / "recurspec"
    assert (installed / "SKILL.md").is_file()
    assert sorted(path.name for path in (installed / "references").iterdir()) == [
        "design.md",
        "reconcile.md",
        "resolve.md",
    ]
