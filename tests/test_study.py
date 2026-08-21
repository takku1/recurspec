import sys
from pathlib import Path

from recurspec.cli import main
from recurspec.study import (
    StudyInstrumentError,
    accept_arm,
    assign_pair,
    check_contamination,
    init_pair,
    is_recurspec_repository,
)


def _assigned_pair(tmp_path: Path, pair_id: str = "locus-01") -> Path:
    subject = tmp_path / "other"
    if not subject.exists():
        subject.mkdir()
        (subject / "pyproject.toml").write_text('name = "other"\n', encoding="utf-8")
    log = init_pair(
        tmp_path,
        pair_id=pair_id,
        project=str(subject),
        task_a="Task A",
        task_b="Task B",
        hours="4h",
        baseline="existing open-work tickets",
    )
    assign_pair(log)
    return log


def _verify(code: str) -> str:
    return f'"{sys.executable}" -c "{code}"'


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


def test_check_contamination_is_clean_for_a_fresh_subject(tmp_path: Path):
    subject = tmp_path / "clean"
    subject.mkdir()
    assert check_contamination(subject, "R-ARCH-13 do the thing", "R-ARCH-14 other thing") == []


def test_check_contamination_finds_an_existing_strategy_handoff(tmp_path: Path):
    subject = tmp_path / "dirty"
    handoffs = subject / ".recurspec" / "handoffs"
    handoffs.mkdir(parents=True)
    (handoffs / "strategy-R-ARCH-13.md").write_text("# Strategy R-ARCH-13\n", encoding="utf-8")

    findings = check_contamination(subject, "R-ARCH-13 catalog priority index", "R-ARCH-14 other")
    assert any("R-ARCH-13" in finding and "strategy handoff" in finding for finding in findings)


def test_check_contamination_finds_a_tracker_reference(tmp_path: Path):
    subject = tmp_path / "dirty-tracker"
    subject.mkdir()
    (subject / "ROADMAP.md").write_text(
        "| R-ARCH-13 | Catalog priority index | active (NEED_CHECKER) | |\n",
        encoding="utf-8",
    )

    findings = check_contamination(subject, "R-ARCH-13 catalog priority index", "R-ARCH-14 other")
    assert any("R-ARCH-13" in finding and "ROADMAP.md" in finding for finding in findings)


def test_check_contamination_ignores_an_adr_id_ending_in_the_ticket_number(tmp_path: Path):
    """`ADR-SR-003` is not a reference to ticket `R-003`; bare containment says it is."""

    subject = tmp_path / "adr-only"
    docs = subject / "docs" / "architecture"
    docs.mkdir(parents=True)
    (docs / "SYSTEM.md").write_text(
        "- **ADR-SR-003:** Query policy consumes one deep Interface.\n"
        "- **ADR-GIR-003:** The IR is not a parallel answer store.\n",
        encoding="utf-8",
    )

    assert check_contamination(subject, "R-003 short-word absence", "R-004 facet ordering") == []


def test_check_contamination_allows_an_unworked_tracker_registration(tmp_path: Path):
    """Protocol section 2 requires a task to be *already prioritized*, so it is already
    registered somewhere. A registration row with no sign of work is eligibility, not
    contamination; flagging it makes every eligible task ineligible."""

    subject = tmp_path / "registered-not-worked"
    subject.mkdir()
    (subject / "ROADMAP.md").write_text(
        "| R-004 | Facet reservations are seated in arrival order | ready | "
        "ordering by facet evidence strength is untried |\n",
        encoding="utf-8",
    )

    assert check_contamination(subject, "R-004 facet ordering", "R-003 short-word absence") == []


def test_check_contamination_finds_a_non_strategy_handoff(tmp_path: Path):
    """A correction or escalation handoff is a Recurspec fingerprint too."""

    subject = tmp_path / "corrected"
    handoffs = subject / ".recurspec" / "handoffs"
    handoffs.mkdir(parents=True)
    (handoffs / "correction-R-010.md").write_text("# Correction R-010\n", encoding="utf-8")

    findings = check_contamination(subject, "R-010 token leak", "R-011 other")
    assert any("R-010" in finding and "handoff" in finding for finding in findings)


def test_study_init_refuses_a_contaminated_subject(tmp_path: Path):
    subject = tmp_path / "other"
    handoffs = subject / ".recurspec" / "handoffs"
    handoffs.mkdir(parents=True)
    (handoffs / "strategy-R-ARCH-13.md").write_text("# Strategy R-ARCH-13\n", encoding="utf-8")
    (subject / "pyproject.toml").write_text('name = "other"\n', encoding="utf-8")

    try:
        init_pair(
            tmp_path,
            pair_id="dirty-01",
            project=str(subject),
            task_a="R-ARCH-13 catalog priority index",
            task_b="R-ARCH-14 other",
            hours="4h",
            baseline="existing open-work tickets",
        )
    except StudyInstrumentError as exc:
        assert "R-ARCH-13" in str(exc)
    else:
        raise AssertionError("expected refuse contaminated subject")
    assert not (tmp_path / "docs" / "research" / "pairs" / "dirty-01.md").exists()


def test_init_pair_refuses_a_task_containing_a_pipe(tmp_path: Path):
    """A '|' in a task/hours field would corrupt the single-line Markdown table row
    and break every later regex-based read/rewrite of the pair log (assign_pair)."""
    subject = tmp_path / "other"
    subject.mkdir()
    (subject / "pyproject.toml").write_text('name = "other"\n', encoding="utf-8")

    try:
        init_pair(
            tmp_path,
            pair_id="unsafe-01",
            project=str(subject),
            task_a="fix parser for `a|b` syntax",
            task_b="B",
            hours="4h",
            baseline="existing open-work tickets",
        )
    except StudyInstrumentError as exc:
        assert "task_a" in str(exc)
    else:
        raise AssertionError("expected refuse a table-unsafe task field")
    assert not (tmp_path / "docs" / "research" / "pairs" / "unsafe-01.md").exists()


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


def test_init_pair_includes_an_arm_start_section(tmp_path: Path):
    subject = tmp_path / "other"
    subject.mkdir()
    log = init_pair(
        tmp_path,
        pair_id="fresh-01",
        project=str(subject),
        task_a="A",
        task_b="B",
        hours="2h",
        baseline="tickets",
    )
    text = log.read_text(encoding="utf-8")
    assert "## Arm start (observed, not a-priori)" in text
    assert "Accepted implementation: no." in text


def test_accept_arm_records_a_passing_verify_command(tmp_path: Path):
    log = _assigned_pair(tmp_path)
    result = accept_arm(
        log,
        arm="recurspec",
        checker="alice@example.com",
        maker="bob@example.com",
        verify_command=_verify("raise SystemExit(0)"),
        cwd=tmp_path,
    )

    assert result.exit_code == 0
    assert result.arm == "recurspec"
    assert result.checker == "alice@example.com"
    assert result.maker == "bob@example.com"
    text = log.read_text(encoding="utf-8")
    assert "alice@example.com" in text
    assert "bob@example.com" in text
    assert "Accepted Recurspec arm:" in text
    assert "exit: 0" in text
    assert "Accepted implementation: yes (Recurspec arm," in text


def test_accept_arm_refuses_a_failing_verify_and_leaves_the_log(tmp_path: Path):
    log = _assigned_pair(tmp_path)
    before = log.read_text(encoding="utf-8")

    try:
        accept_arm(
            log,
            arm="baseline",
            checker="alice",
            maker="bob",
            verify_command=_verify("raise SystemExit(1)"),
            cwd=tmp_path,
        )
    except StudyInstrumentError as exc:
        assert "exit 1" in str(exc)
    else:
        raise AssertionError("expected refuse failing verify")
    assert log.read_text(encoding="utf-8") == before


def test_accept_arm_refuses_same_identity_before_running_verify(tmp_path: Path):
    log = _assigned_pair(tmp_path)
    marker = tmp_path / "ran"
    before = log.read_text(encoding="utf-8")

    try:
        accept_arm(
            log,
            arm="recurspec",
            checker="same-person",
            maker="same-person",
            verify_command=_verify(
                f"from pathlib import Path; Path(r'{marker}').write_text('ran')"
            ),
            cwd=tmp_path,
        )
    except StudyInstrumentError as exc:
        assert "must differ" in str(exc)
    else:
        raise AssertionError("expected refuse self-accept")
    assert not marker.exists()
    assert log.read_text(encoding="utf-8") == before


def test_study_accept_cli(tmp_path: Path, capsys):
    log = _assigned_pair(tmp_path, pair_id="cli-01")
    code = main(
        [
            "study",
            "accept",
            str(log),
            "--arm",
            "baseline",
            "--checker",
            "checker",
            "--maker",
            "maker",
            "--verify",
            _verify("raise SystemExit(0)"),
            "--cwd",
            str(tmp_path),
        ]
    )

    assert code == 0
    output = capsys.readouterr().out
    assert "cli-01" in output
    assert "baseline" in output
    text = log.read_text(encoding="utf-8")
    assert "Accepted Baseline arm:" in text
