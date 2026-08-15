import json
from pathlib import Path

import pytest

from recurspec import cli
from recurspec.cli import _skill_targets, build_parser, main, sync_skill


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
    skills = parser.parse_args(["skills", "check", "--target", "grok"])
    contract = parser.parse_args(["contract", "check", "docs"])
    contract_evidence = parser.parse_args(
        ["contract", "evidence", "docs", "--format", "json"]
    )
    structure = parser.parse_args(["structure", "check", ".", "--format", "json"])
    reconcile = parser.parse_args(["reconcile", "plan", ".", "--format", "json"])
    stack = parser.parse_args(["stack", "check", ".", "--format", "json"])
    modules = parser.parse_args(
        ["modules", "check", ".", "--changed-file", "src/recurspec/contract.py"]
    )
    frontier = parser.parse_args(["frontier", "check", ".", "--format", "json"])
    status = parser.parse_args(["status", ".", "--format", "json"])
    fanout = parser.parse_args(
        ["fanout", "--item", "one", "--item", "two", "--write"]
    )
    corpus = parser.parse_args(
        ["corpus", "export", "--output", "corpus.jsonl", "--i-opt-in"]
    )
    predict = parser.parse_args(["predict", "checkout", "--format", "json"])
    recommend = parser.parse_args(["recommend"])
    study_accept = parser.parse_args(
        [
            "study",
            "accept",
            "pair.md",
            "--arm",
            "recurspec",
            "--checker",
            "alice",
            "--maker",
            "bob",
            "--verify",
            "pytest",
        ]
    )

    assert evaluate.module == "checkout"
    assert evaluate.candidate_branch == "candidate/42"
    assert evaluate.worker_state == Path("worker-state.json")
    assert evaluate.authorization_id == "node-42"
    assert skills.action == "check"
    assert skills.target == "grok"
    assert contract.action == "check"
    assert structure.action == "check"
    assert structure.format == "json"
    assert reconcile.action == "plan"
    assert stack.action == "check"
    assert modules.action == "check"
    assert modules.changed_file == ["src/recurspec/contract.py"]
    assert frontier.action == "check"
    assert status.repository == Path(".")
    assert status.format == "json"
    assert fanout.item == ["one", "two"]
    assert fanout.write is True
    assert corpus.action == "export"
    assert corpus.i_opt_in is True
    assert predict.module == "checkout"
    assert predict.format == "json"
    assert recommend.corpus is None
    assert contract.path == Path("docs")
    assert contract_evidence.action == "evidence"
    assert contract_evidence.path == Path("docs")
    assert contract_evidence.format == "json"
    assert study_accept.action == "accept"
    assert study_accept.arm == "recurspec"
    assert study_accept.checker == "alice"
    assert study_accept.maker == "bob"
    assert study_accept.verify == "pytest"


@pytest.mark.parametrize("bad_tolerance", ["nan", "inf", "-1"])
def test_evaluate_cli_rejects_non_finite_or_negative_tolerance(bad_tolerance, capsys):
    parser = build_parser()

    with pytest.raises(SystemExit):
        parser.parse_args(
            [
                "evaluate",
                "checkout",
                "candidate/42",
                "--worker-state",
                "worker-state.json",
                "--authorization-id",
                "node-42",
                "--tolerance",
                bad_tolerance,
            ]
        )
    assert "must be a finite, non-negative number" in capsys.readouterr().err


def test_every_cli_argument_documents_itself():
    parser = build_parser()

    def actions(subparser):
        return [action for action in subparser._actions if action.dest != "help"]

    evaluate = parser._subparsers._group_actions[0].choices["evaluate"]
    predict = parser._subparsers._group_actions[0].choices["predict"]
    recommend = parser._subparsers._group_actions[0].choices["recommend"]
    skills = parser._subparsers._group_actions[0].choices["skills"]
    status = parser._subparsers._group_actions[0].choices["status"]
    fanout = parser._subparsers._group_actions[0].choices["fanout"]
    contract = parser._subparsers._group_actions[0].choices["contract"]
    check = contract._subparsers._group_actions[0].choices["check"]
    contract_evidence = contract._subparsers._group_actions[0].choices["evidence"]
    modules_check = (
        parser._subparsers._group_actions[0]
        .choices["modules"]
        ._subparsers._group_actions[0]
        .choices["check"]
    )
    corpus_export = (
        parser._subparsers._group_actions[0]
        .choices["corpus"]
        ._subparsers._group_actions[0]
        .choices["export"]
    )
    study_accept = (
        parser._subparsers._group_actions[0]
        .choices["study"]
        ._subparsers._group_actions[0]
        .choices["accept"]
    )

    for subparser in (
        evaluate,
        predict,
        recommend,
        skills,
        status,
        fanout,
        check,
        contract_evidence,
        modules_check,
        corpus_export,
        study_accept,
    ):
        for action in actions(subparser):
            assert action.help, f"{subparser.prog} {action.dest} is missing help text"


def test_corpus_export_cli_refuses_without_opt_in(tmp_path: Path, capsys):
    code = main(["corpus", "export", "--output", str(tmp_path / "corpus.jsonl")])

    assert code == 2
    assert "opt-in" in capsys.readouterr().err


def test_predict_cli_refuses_without_negative_patterns(tmp_path: Path, capsys):
    code = main(["predict", "checkout", "--log-dir", str(tmp_path / "empty")])

    assert code == 1
    assert "refuse to invent" in capsys.readouterr().err


def test_recommend_cli_refuses_to_invent_a_decision_class(capsys):
    assert main(["recommend"]) == 1
    assert "refusing to invent" in capsys.readouterr().err


def test_skill_targets_include_grok_under_grok_home(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    grok_home = tmp_path / "grok-home"
    monkeypatch.setenv("GROK_HOME", str(grok_home))

    grok_only = _skill_targets("grok")
    everyone = _skill_targets("all")

    assert grok_only == [("Grok", grok_home / "skills")]
    assert ("Grok", grok_home / "skills") in everyone
    assert {label for label, _path in everyone} == {"Claude Code", "Codex", "Grok"}


def test_skills_install_writes_the_bundled_skill_to_grok_home(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys
):
    grok_home = tmp_path / "grok-home"
    monkeypatch.setenv("GROK_HOME", str(grok_home))

    assert main(["skills", "install", "--target", "grok"]) == 0
    assert (grok_home / "skills" / "recurspec" / "SKILL.md").is_file()
    assert "Grok:" in capsys.readouterr().out
    assert main(["skills", "check", "--target", "grok"]) == 0


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


def test_evaluate_cli_bks_metrics_only_still_runs_the_full_evaluation(tmp_path, monkeypatch, capsys):
    """Locks in current behavior: --bks-metrics-only only changes what the printed
    BKS packet contains (metrics vs. metrics+source, per implementor_bks); it does
    not turn `evaluate` into a print-and-exit command. The isolated candidate
    evaluation - including its worktree lifecycle and possible merge - still runs."""
    evaluate_calls = []

    def evaluate(repo, module, branch, **kwargs):
        evaluate_calls.append((repo, module, branch))
        return 0, "passed"

    monkeypatch.setattr(cli, "evaluate_isolated_candidate", evaluate)
    monkeypatch.setattr(cli, "load_merge_authorization", lambda *_args: object())

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
            "--bks-metrics-only",
        ]
    )

    assert code == 0
    assert len(evaluate_calls) == 1
    packet = json.loads(capsys.readouterr().out.splitlines()[0])
    assert packet["metrics_only"] is True
    assert packet["source_excerpts"] == []


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
