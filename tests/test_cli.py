from pathlib import Path

from recurspec.cli import build_parser, main, sync_skill


def test_parser_exposes_the_public_commands():
    parser = build_parser()

    evaluate = parser.parse_args(["evaluate", "checkout", "candidate/42"])
    skills = parser.parse_args(["skills", "check", "--target", "codex"])
    contract = parser.parse_args(["contract", "check", "docs"])

    assert evaluate.module == "checkout"
    assert evaluate.candidate_branch == "candidate/42"
    assert skills.action == "check"
    assert skills.target == "codex"
    assert contract.action == "check"
    assert contract.path == Path("docs")


def test_every_cli_argument_documents_itself():
    parser = build_parser()

    def actions(subparser):
        return [action for action in subparser._actions if action.dest != "help"]

    evaluate = parser._subparsers._group_actions[0].choices["evaluate"]
    skills = parser._subparsers._group_actions[0].choices["skills"]
    contract = parser._subparsers._group_actions[0].choices["contract"]
    check = contract._subparsers._group_actions[0].choices["check"]

    for subparser in (evaluate, skills, check):
        for action in actions(subparser):
            assert action.help, f"{subparser.prog} {action.dest} is missing help text"


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


def test_contract_check_cli_uses_distinct_valid_invalid_and_instrument_exit_codes(capsys):
    fixtures = Path(__file__).parent / "fixtures" / "contracts"

    assert main(["contract", "check", str(fixtures / "valid"), "--format", "json"]) == 0
    valid_payload = capsys.readouterr().out
    assert valid_payload == '{"contracts_checked":1,"diagnostics":[],"valid":true}\n'

    assert main(["contract", "check", str(fixtures / "invalid-invariant")]) == 1
    invalid_output = capsys.readouterr().out
    assert "contract.invariant.ears" in invalid_output
    assert "contract.invariant.evidence-stage" in invalid_output

    assert main(["contract", "check", str(fixtures / "does-not-exist")]) == 2
    assert "contract validation instrument failed" in capsys.readouterr().err


def test_contract_check_cli_rejects_an_empty_directory(tmp_path: Path, capsys):
    assert main(["contract", "check", str(tmp_path)]) == 1
    assert "contract.discovery.empty" in capsys.readouterr().out
