import json
from pathlib import Path

from recurspec import cli
from recurspec.cli import build_parser, main, sync_skill


def test_parser_exposes_the_public_commands():
    parser = build_parser()

    evaluate = parser.parse_args(
        [
            "evaluate",
            "checkout",
            "candidate/42",
            "--worker-state",
            "worker-state.json",
            "--authorization-id",
            "node-42",
        ]
    )
    skills = parser.parse_args(["skills", "check", "--target", "codex"])
    contract = parser.parse_args(["contract", "check", "docs"])
    structure = parser.parse_args(["structure", "check", ".", "--format", "json"])
    reconcile = parser.parse_args(["reconcile", "plan", ".", "--format", "json"])
    stack = parser.parse_args(["stack", "check", ".", "--format", "json"])

    assert evaluate.module == "checkout"
    assert evaluate.candidate_branch == "candidate/42"
    assert evaluate.worker_state == Path("worker-state.json")
    assert evaluate.authorization_id == "node-42"
    assert skills.action == "check"
    assert skills.target == "codex"
    assert contract.action == "check"
    assert structure.action == "check"
    assert structure.format == "json"
    assert reconcile.action == "plan"
    assert stack.action == "check"
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


def test_evaluate_cli_orchestrates_the_isolated_candidate_lifecycle(tmp_path, monkeypatch):
    received = {}

    def evaluate(repo, module, branch, **kwargs):
        received.update(repo=repo, module=module, branch=branch, **kwargs)
        return 0, "passed"

    monkeypatch.setattr(cli, "evaluate_isolated_candidate", evaluate)
    authorization = object()
    monkeypatch.setattr(cli, "load_merge_authorization", lambda *_args: authorization)

    code = main(
        [
            "evaluate",
            "checkout",
            "candidate/R-200",
            "--worker-state",
            str(tmp_path / "worker-state.json"),
            "--authorization-id",
            "R-200",
            "--repo",
            str(tmp_path),
            "--record-baseline",
        ]
    )

    assert code == 0
    assert Path(received["repo"]) == tmp_path
    assert received["module"] == "checkout"
    assert received["branch"] == "candidate/R-200"
    assert received["authorization"] is authorization
    assert received["record_baseline"] is True


def test_structure_check_cli_emits_stable_json_and_distinct_exit_codes(tmp_path, capsys):
    (tmp_path / "src").mkdir()
    (tmp_path / "docs" / "architecture").mkdir(parents=True)
    orphan = tmp_path / "src" / "orphan.py"
    orphan.write_text("def visible():\n    pass\n", encoding="utf-8")

    code = main(
        [
            "structure",
            "check",
            str(tmp_path),
            "--source-root",
            "src",
            "--contract-root",
            "docs/architecture",
            "--format",
            "json",
        ]
    )

    assert code == 1
    assert capsys.readouterr().out == (
        '{"diagnostics":[{"code":"structure.public.uncontracted",'
        '"message":"public symbol has no parent Contract Node","path":"src/orphan.py",'
        '"symbol":"visible"}],"instrument_error":false,"valid":false}\n'
    )


def test_reconcile_plan_cli_emits_drafts_without_writing_them(tmp_path, capsys):
    source = tmp_path / "src" / "recurspec"
    source.mkdir(parents=True)
    (tmp_path / "tests").mkdir()
    (tmp_path / "docs" / "architecture").mkdir(parents=True)
    (source / "orphan.py").write_text("def visible():\n    pass\n", encoding="utf-8")

    code = main(["reconcile", "plan", str(tmp_path), "--format", "json"])

    payload = json.loads(capsys.readouterr().out)
    assert code == 1
    assert payload["actions"][0]["kind"] == "draft_leaf"
    assert payload["deferred_empirical_events"] == 0
    assert not (tmp_path / payload["actions"][0]["contract_path"]).exists()
