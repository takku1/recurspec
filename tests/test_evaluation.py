#!/usr/bin/env python3
"""Behavioral checks for the Recurspec Evaluation Gate."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from recurspec import evaluation as gate
from recurspec.evidence import log_event
from recurspec.metrics import (
    HARD_GATE,
    IMPROVED,
    NEUTRAL,
    OBSERVATION,
    OPTIMIZATION,
    REGRESSED,
    TARGET,
    UNKNOWN,
    EvidenceInstrumentError,
    compare,
    count_consecutive_reverts,
    count_total_reverts,
    evaluate_candidate,
    find_baseline,
    parse_measurement,
    read_events,
    read_negative_patterns,
    resolve_direction,
    resolve_tier,
    telemetry_contradiction,
)
from recurspec.spec_runner.workers import RuntimeResponse, WorkerPool


def _independent_review(repo: Path):
    pool = WorkerPool(lambda *_args: RuntimeResponse({"approved": True}, 1, 1, 1.0), concurrency=1)
    pool.dispatch("R-200", {}, "frame", "worker-1", 100)
    branch = "candidate/R-200"
    oid = _git(repo, "rev-parse", branch)
    pool.dispatch("R-200", {}, "check", "worker-2", 100, branch, oid)
    return pool.merge_authorization(
        "R-200"
    )


def _git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


_TRUSTED_CHECKS_SH = """#!/usr/bin/env bash
set -euo pipefail
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
if grep -q "broken" "${DIR}/state.txt" 2>/dev/null; then
  echo "state is broken" >&2
  exit 1
fi
exit 0
"""

_TRUSTED_MEASURE_SH = """#!/usr/bin/env bash
set -euo pipefail
printf '{"metric":"m","value":1,"direction":"higher","status":"success"}\\n'
"""


def _repo_with_candidate(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-b", "main", str(repo)], check=True, capture_output=True)
    _git(repo, "config", "user.email", "tests@example.invalid")
    _git(repo, "config", "user.name", "Recurspec Tests")
    (repo / "state.txt").write_text("baseline\n", encoding="utf-8")
    modules = repo / "modules" / "checkout"
    modules.mkdir(parents=True)
    (modules / "checks.sh").write_text(_TRUSTED_CHECKS_SH, encoding="utf-8")
    (modules / "measure.sh").write_text(_TRUSTED_MEASURE_SH, encoding="utf-8")
    _git(repo, "add", "state.txt", "modules")
    _git(repo, "commit", "-m", "baseline")
    _git(repo, "switch", "-c", "candidate/R-200")
    (repo / "state.txt").write_text("candidate\n", encoding="utf-8")
    _git(repo, "add", "state.txt")
    _git(repo, "commit", "-m", "candidate")
    _git(repo, "switch", "main")
    return repo

# --- direction resolution ---------------------------------------------------


@pytest.mark.parametrize(
    "metric,expected",
    [
        ("latency_p99_ms", "lower"),
        ("build_duration", "lower"),
        ("memory_bytes", "lower"),
        ("error_rate", "lower"),  # 'error' must dominate 'rate'
        ("ears_validation_pass_rate", "higher"),
        ("specs_generated_per_sec", "higher"),
        ("coverage", "higher"),
        ("wibble", None),  # undecidable -> must not guess
    ],
)
def test_resolve_direction(metric, expected):
    assert resolve_direction(metric) == expected


def test_declared_direction_overrides_inference():
    assert resolve_direction("latency_p99_ms", "higher") == "higher"


def test_bad_declared_direction_raises():
    with pytest.raises(ValueError):
        resolve_direction("latency_p99_ms", "sideways")


# --- comparison -------------------------------------------------------------


def test_lower_is_better_improvement():
    c = compare("latency_p99_ms", 80.0, 100.0)
    assert c.verdict == IMPROVED
    assert c.delta_pct == pytest.approx(20.0)


def test_lower_is_better_regression_beyond_tolerance():
    c = compare("latency_p99_ms", 130.0, 100.0, tolerance_pct=20.0)
    assert c.verdict == REGRESSED
    assert c.blocks_merge


def test_lower_is_better_regression_within_tolerance_is_neutral():
    c = compare("latency_p99_ms", 110.0, 100.0, tolerance_pct=20.0)
    assert c.verdict == NEUTRAL
    assert not c.blocks_merge


def test_higher_is_better_regression_is_caught():
    # The pre-fix evaluator had no direction awareness; a pass-rate drop from
    # 1.0 to 0.5 would have read as an improvement under a naive `<=`.
    c = compare("ears_validation_pass_rate", 0.5, 1.0, tolerance_pct=20.0)
    assert c.verdict == REGRESSED


def test_higher_is_better_improvement():
    assert compare("throughput_ops_per_sec", 150.0, 100.0).verdict == IMPROVED


def test_noise_band_is_neutral():
    assert compare("latency_p99_ms", 100.5, 100.0).verdict == NEUTRAL


def test_absent_baseline_is_neutral_not_improved():
    c = compare("latency_p99_ms", 42.0, None)
    assert c.verdict == NEUTRAL
    assert c.baseline is None


def test_undecidable_direction_blocks_merge():
    c = compare("wibble", 10.0, 5.0)
    assert c.verdict == UNKNOWN
    assert c.blocks_merge


def test_non_numeric_current_is_unknown():
    assert compare("latency_p99_ms", "fast", 100.0).verdict == UNKNOWN


def test_zero_baseline_compares_by_sign():
    assert compare("error_count", 3.0, 0.0).verdict == REGRESSED
    assert compare("error_count", 0.0, 0.0).verdict == NEUTRAL


# --- measurement parsing ----------------------------------------------------


PRETTY_TEMPLATE_OUTPUT = """{
  "ts": "2026-08-04T00:00:00Z",
  "event_type": "measurement",
  "module": "contract-engine",
  "metric": "latency_p99_ms",
  "value": 42.5,
  "unit": "ms",
  "evidence_stage": "Measured",
  "status": "success"
}"""


def test_parses_pretty_printed_template_output():
    # Regression guard: the previous parser took the last line starting with
    # '{', which for this payload is the opening brace alone.
    payload = parse_measurement(PRETTY_TEMPLATE_OUTPUT)
    assert payload["metric"] == "latency_p99_ms"
    assert payload["value"] == 42.5


def test_parses_payload_after_log_noise():
    out = "[measure] warming up\n[measure] 3 iterations\n" + PRETTY_TEMPLATE_OUTPUT
    assert parse_measurement(out)["value"] == 42.5


def test_unparseable_output_raises_rather_than_fabricating():
    with pytest.raises(ValueError):
        parse_measurement("no json here at all")
    with pytest.raises(ValueError):
        parse_measurement("")


# --- telemetry honesty ------------------------------------------------------


def test_clean_payload_has_no_contradiction():
    assert telemetry_contradiction(json.loads(PRETTY_TEMPLATE_OUTPUT)) is None


def test_success_without_value_is_a_contradiction():
    assert telemetry_contradiction({"metric": "x", "status": "success"}) is not None


def test_failure_status_is_a_contradiction():
    assert telemetry_contradiction({"metric": "x", "value": 1, "status": "error"}) is not None


def test_overclaimed_evidence_stage_is_a_contradiction():
    # An evaluation cannot yield Proved (research foundations SS5).
    assert (
        telemetry_contradiction({"metric": "x", "value": 1, "evidence_stage": "Proved"}) is not None
    )


def test_nan_value_is_a_contradiction_not_a_manufactured_measurement():
    # Reproduces the review's exact repro: a NaN reading must never compare as a
    # tolerated regression - it must never reach compare() at all.
    assert telemetry_contradiction({"metric": "latency_ms", "value": float("nan")}) is not None
    assert telemetry_contradiction({"metric": "latency_ms", "value": float("inf")}) is not None


def test_missing_metric_name_is_a_contradiction():
    assert telemetry_contradiction({"value": 1, "status": "success"}) is not None


def test_bad_declared_direction_is_a_contradiction_not_an_uncaught_exception():
    assert telemetry_contradiction({"metric": "x", "value": 1, "direction": "sideways"}) is not None


def test_bad_declared_tier_is_a_contradiction_not_an_uncaught_exception():
    bad = {"metric": "x", "value": 1, "tier": "vibes"}
    assert telemetry_contradiction(bad) is not None
    bad_multi = {"status": "success", "metrics": [{"metric": "x", "value": 1, "tier": "vibes"}]}
    assert telemetry_contradiction(bad_multi) is not None


def test_evaluation_gate_reverts_a_nan_measurement_instead_of_keeping(tmp_path, monkeypatch):
    payload = {"metric": "latency_ms", "value": float("nan"), "status": "success"}
    script_results = iter([(0, "", ""), (0, json.dumps(payload, allow_nan=True), "")])
    monkeypatch.setattr(gate, "run_script", lambda *_args, **_kwargs: next(script_results))

    code, reason = gate.evaluate_change("checkout", "candidate/R-102", log_dir=str(tmp_path))

    assert code == gate.REVERT
    assert "telemetry contradiction" in reason


def test_compare_rejects_non_finite_or_negative_tolerance():
    with pytest.raises(ValueError):
        compare("latency_ms", 100.0, 100.0, tolerance_pct=float("nan"))
    with pytest.raises(ValueError):
        compare("latency_ms", 100.0, 100.0, tolerance_pct=float("inf"))
    with pytest.raises(ValueError):
        compare("latency_ms", 100.0, 100.0, tolerance_pct=-1.0)
    with pytest.raises(ValueError):
        compare("latency_ms", 100.0, 100.0, noise_pct=float("nan"))


def test_read_events_survives_only_a_torn_final_line(tmp_path):
    from recurspec.metrics import read_events

    log_dir = str(tmp_path)
    log_event("comp", "baseline", {"metric": "m", "value": 1.0}, branch="main", log_dir=log_dir)
    log_path = os.path.join(log_dir, "comp", "log.jsonl")
    # log_event() always terminates a completed append with "\n"; a write interrupted
    # mid-flush leaves the file *without* one. That absence is what makes this line
    # distinguishable from real corruption (R-602) - it must not end in a newline.
    with open(log_path, "a", encoding="utf-8") as f:
        f.write('{"ts": "trunc')

    assert len(read_events("comp", log_dir)) == 1


def test_read_events_raises_on_corruption_that_is_not_the_final_line(tmp_path):
    from recurspec.metrics import read_events

    log_dir = str(tmp_path)
    comp_dir = tmp_path / "comp"
    comp_dir.mkdir()
    log_path = comp_dir / "log.jsonl"
    log_path.write_text(
        '{"broken\n{"event_type": "baseline", "branch": "main"}\n', encoding="utf-8"
    )

    with pytest.raises(EvidenceInstrumentError):
        read_events("comp", log_dir)


def test_read_events_raises_on_a_complete_but_corrupt_final_line(tmp_path):
    """A newline-terminated final line is a completed append, not a torn one - even
    when it is the very last line in the file, its corruption is real and must not be
    forgiven the way a torn write is (R-602)."""
    from recurspec.metrics import read_events

    log_dir = str(tmp_path)
    comp_dir = tmp_path / "comp"
    comp_dir.mkdir()
    log_path = comp_dir / "log.jsonl"
    log_path.write_text(
        json.dumps(
            {
                "ts": "2026-01-01T00:00:00+00:00",
                "event_type": "baseline",
                "module": "comp",
                "branch": "main",
                "evidence_stage": "Measured",
                "metrics": {},
            }
        )
        + "\n"
        '{"not valid json\n',
        encoding="utf-8",
    )

    with pytest.raises(EvidenceInstrumentError):
        read_events("comp", log_dir)


def test_read_events_raises_on_a_non_object_json_scalar(tmp_path):
    """A line that parses as valid JSON but isn't an object (e.g. a bare number) must
    not silently enter the event stream, where a later ``.get()`` call would crash with
    AttributeError instead of failing closed (R-602)."""
    from recurspec.metrics import read_events

    log_dir = str(tmp_path)
    comp_dir = tmp_path / "comp"
    comp_dir.mkdir()
    log_path = comp_dir / "log.jsonl"
    log_path.write_text(
        json.dumps(
            {
                "ts": "2026-01-01T00:00:00+00:00",
                "event_type": "baseline",
                "module": "comp",
                "branch": "main",
                "evidence_stage": "Measured",
                "metrics": {},
            }
        )
        + "\n"
        "42\n",
        encoding="utf-8",
    )

    with pytest.raises(EvidenceInstrumentError):
        read_events("comp", log_dir)


def test_read_events_raises_on_an_empty_object(tmp_path):
    from recurspec.metrics import read_events

    log_dir = str(tmp_path)
    comp_dir = tmp_path / "comp"
    comp_dir.mkdir()
    (comp_dir / "log.jsonl").write_text("{}\n", encoding="utf-8")

    with pytest.raises(EvidenceInstrumentError, match="missing"):
        read_events("comp", log_dir)


def _write_one_event(tmp_path: Path, **overrides) -> str:
    event = {
        "ts": "2026-01-01T00:00:00+00:00",
        "event_type": "baseline",
        "module": "comp",
        "branch": "main",
        "evidence_stage": "Measured",
        "metrics": {},
    }
    event.update(overrides)
    log_dir = str(tmp_path)
    comp_dir = tmp_path / "comp"
    comp_dir.mkdir()
    (comp_dir / "log.jsonl").write_text(json.dumps(event) + "\n", encoding="utf-8")
    return log_dir


def test_read_events_raises_on_a_module_that_disagrees_with_its_own_log(tmp_path):
    """An event whose ``module`` field names a different module than the log it lives
    in was never legitimately written there (R-641)."""
    from recurspec.metrics import read_events

    log_dir = _write_one_event(tmp_path, module="a-different-module")

    with pytest.raises(EvidenceInstrumentError, match="module"):
        read_events("comp", log_dir)


def test_read_events_raises_on_an_unrecognized_event_type(tmp_path):
    """A made-up event_type is a spoofed or invented event, not corruption to forgive
    (R-641)."""
    from recurspec.metrics import read_events

    log_dir = _write_one_event(tmp_path, event_type="made_up_event")

    with pytest.raises(EvidenceInstrumentError, match="event_type"):
        read_events("comp", log_dir)


def test_read_events_raises_on_an_unparseable_timestamp(tmp_path):
    from recurspec.metrics import read_events

    log_dir = _write_one_event(tmp_path, ts="not-a-timestamp")

    with pytest.raises(EvidenceInstrumentError, match="timestamp"):
        read_events("comp", log_dir)


def test_find_baseline_raises_rather_than_silently_dropping_a_corrupt_prior_baseline(tmp_path):
    # Reproduces the review's exact scenario: the only baseline event is corrupt, and a
    # later measurement follows it - this must not read back as "no baseline yet".
    log_dir = str(tmp_path)
    comp_dir = tmp_path / "comp"
    comp_dir.mkdir()
    log_path = comp_dir / "log.jsonl"
    log_path.write_text(
        '{"event_type": "baseline", "branch": "main", "not valid json\n'
        + json.dumps({"event_type": "measurement", "branch": "main", "metrics": {}})
        + "\n",
        encoding="utf-8",
    )

    with pytest.raises(EvidenceInstrumentError):
        find_baseline("comp", "latency_p99_ms", log_dir)


# --- evidence log round-trip ------------------------------------------------


def test_find_baseline_ignores_candidate_branches(tmp_path):
    log_dir = str(tmp_path)
    log_event(
        "comp",
        "baseline",
        {"metric": "latency_p99_ms", "value": 100.0},
        branch="main",
        log_dir=log_dir,
    )
    log_event(
        "comp",
        "measurement",
        {"metric": "latency_p99_ms", "value": 10.0},
        branch="candidate/R-001",
        log_dir=log_dir,
    )

    found = find_baseline("comp", "latency_p99_ms", log_dir)
    assert found["metrics"]["value"] == 100.0, "a reverted branch must not set the bar"


def test_find_baseline_takes_most_recent_and_matches_metric(tmp_path):
    log_dir = str(tmp_path)
    log_event(
        "comp",
        "baseline",
        {"metric": "latency_p99_ms", "value": 100.0},
        branch="main",
        log_dir=log_dir,
    )
    log_event(
        "comp", "baseline", {"metric": "other_metric", "value": 7.0}, branch="main", log_dir=log_dir
    )
    log_event(
        "comp",
        "baseline",
        {"metric": "latency_p99_ms", "value": 90.0},
        branch="main",
        log_dir=log_dir,
    )

    assert find_baseline("comp", "latency_p99_ms", log_dir)["metrics"]["value"] == 90.0
    assert find_baseline("comp", "missing", log_dir) is None


def test_find_baseline_survives_torn_line(tmp_path):
    log_dir = str(tmp_path)
    log_event("comp", "baseline", {"metric": "m", "value": 5.0}, branch="main", log_dir=log_dir)
    # No trailing newline: a completed append always has one (R-602), so this models a
    # genuine mid-write crash rather than a merely malformed but complete event.
    with open(os.path.join(log_dir, "comp", "log.jsonl"), "a", encoding="utf-8") as f:
        f.write('{"ts": "trunc')
    assert find_baseline("comp", "m", log_dir)["metrics"]["value"] == 5.0


def test_log_event_rejects_invalid_stage(tmp_path):
    with pytest.raises(ValueError):
        log_event("comp", "measurement", {}, evidence_stage="Vibes", log_dir=str(tmp_path))


# --- metric tiers -------------------------------------------------------


def test_resolve_tier_defaults_to_hard_gate():
    assert resolve_tier(None) == HARD_GATE
    assert resolve_tier("") == HARD_GATE


@pytest.mark.parametrize(
    "declared,expected",
    [
        ("hard_gate", HARD_GATE),
        ("HARD-GATE", HARD_GATE),
        ("target", TARGET),
        ("optimization", OPTIMIZATION),
        ("observation", OBSERVATION),
    ],
)
def test_resolve_tier_normalizes(declared, expected):
    assert resolve_tier(declared) == expected


def test_resolve_tier_rejects_unknown():
    with pytest.raises(ValueError):
        resolve_tier("vibes")


# --- multi-metric dominance ----------------------------------------------


def _make_comparison(verdict, metric="m"):
    from recurspec.metrics import Comparison

    return Comparison(verdict, metric, 1.0, 1.0, 0.0, "lower", "synthetic")


def test_evaluate_candidate_empty_is_accepted():
    result = evaluate_candidate([])
    assert result.accepted


def test_evaluate_candidate_hard_gate_regression_blocks():
    comparisons = [
        ("latency", _make_comparison(REGRESSED, "latency"), HARD_GATE),
        ("throughput", _make_comparison(IMPROVED, "throughput"), OPTIMIZATION),
    ]
    result = evaluate_candidate(comparisons)
    assert not result.accepted
    assert "latency" in result.blocking


def test_evaluate_candidate_target_regression_blocks_even_if_hard_gate_passes():
    comparisons = [
        ("correctness", _make_comparison(NEUTRAL, "correctness"), HARD_GATE),
        ("p99", _make_comparison(REGRESSED, "p99"), TARGET),
    ]
    result = evaluate_candidate(comparisons)
    assert not result.accepted
    assert "p99" in result.regressed


def test_evaluate_candidate_observation_never_blocks():
    comparisons = [
        ("correctness", _make_comparison(NEUTRAL, "correctness"), HARD_GATE),
        ("log_volume", _make_comparison(REGRESSED, "log_volume"), OBSERVATION),
    ]
    result = evaluate_candidate(comparisons)
    assert result.accepted
    assert result.regressed == []


def test_evaluate_candidate_dominant_when_something_improves():
    comparisons = [
        ("correctness", _make_comparison(NEUTRAL, "correctness"), HARD_GATE),
        ("throughput", _make_comparison(IMPROVED, "throughput"), OPTIMIZATION),
    ]
    result = evaluate_candidate(comparisons)
    assert result.accepted
    assert "throughput" in result.improved


def test_evaluate_candidate_neutral_all_tiers_is_accepted_without_improvement():
    # Mirrors compare()'s own semantics: NEUTRAL keeps, it does not have to win.
    comparisons = [
        ("correctness", _make_comparison(NEUTRAL, "correctness"), HARD_GATE),
        ("throughput", _make_comparison(NEUTRAL, "throughput"), OPTIMIZATION),
    ]
    result = evaluate_candidate(comparisons)
    assert result.accepted
    assert result.improved == []


def test_evaluate_candidate_unknown_at_hard_gate_blocks():
    comparisons = [("x", _make_comparison(UNKNOWN, "x"), HARD_GATE)]
    result = evaluate_candidate(comparisons)
    assert not result.accepted
    assert "x" in result.blocking


# --- multi-metric payload parsing / telemetry -----------------------------


MULTI_METRIC_PAYLOAD = {
    "status": "success",
    "metrics": [
        {
            "metric": "latency_p99_ms",
            "value": 42.5,
            "tier": "hard_gate",
            "evidence_stage": "Measured",
        },
        {
            "metric": "throughput_ops_per_sec",
            "value": 900,
            "tier": "optimization",
            "evidence_stage": "Measured",
        },
    ],
}


def test_parse_measurement_accepts_multi_metric_payload():
    text = json.dumps(MULTI_METRIC_PAYLOAD)
    payload = parse_measurement(text)
    assert isinstance(payload["metrics"], list)
    assert payload["metrics"][0]["metric"] == "latency_p99_ms"


def test_parse_measurement_accepts_multi_metric_after_log_noise():
    out = "[measure] starting\n" + json.dumps(MULTI_METRIC_PAYLOAD)
    payload = parse_measurement(out)
    assert len(payload["metrics"]) == 2


def test_telemetry_contradiction_clean_multi_metric_payload():
    assert telemetry_contradiction(MULTI_METRIC_PAYLOAD) is None


def test_telemetry_contradiction_multi_metric_missing_value():
    bad = {
        "status": "success",
        "metrics": [{"metric": "latency_p99_ms", "evidence_stage": "Measured"}],
    }
    assert telemetry_contradiction(bad) is not None


def test_telemetry_contradiction_multi_metric_overclaimed_stage():
    bad = {
        "status": "success",
        "metrics": [{"metric": "x", "value": 1, "evidence_stage": "Proved"}],
    }
    assert telemetry_contradiction(bad) is not None


# --- negative-pattern buffer ----------------------------------------------


def test_read_negative_patterns_empty_when_none_logged(tmp_path):
    assert read_negative_patterns("comp", str(tmp_path)) == []


def test_read_negative_patterns_returns_logged_entries(tmp_path):
    log_dir = str(tmp_path)
    log_event(
        "comp",
        "negative_pattern",
        {},
        evidence_stage="Refuted",
        branch="candidate/R-001",
        verdict="revert",
        reason="checks.sh failed",
        log_dir=log_dir,
    )
    log_event(
        "comp",
        "decision",
        {},
        evidence_stage="Measured",
        branch="candidate/R-001",
        verdict="keep",
        log_dir=log_dir,
    )

    patterns = read_negative_patterns("comp", log_dir)
    assert len(patterns) == 1
    assert patterns[0]["reason"] == "checks.sh failed"


# --- escalation boundaries -------------------------------------------------


def test_count_consecutive_reverts_zero_when_log_empty(tmp_path):
    assert count_consecutive_reverts("comp", str(tmp_path)) == 0


def test_count_consecutive_reverts_counts_since_last_keep(tmp_path):
    log_dir = str(tmp_path)
    log_event("comp", "decision", {}, branch="candidate/x", verdict="keep", log_dir=log_dir)
    log_event("comp", "decision", {}, branch="candidate/x", verdict="revert", log_dir=log_dir)
    log_event("comp", "decision", {}, branch="candidate/x", verdict="revert", log_dir=log_dir)
    log_event("comp", "decision", {}, branch="candidate/x", verdict="revert", log_dir=log_dir)

    assert count_consecutive_reverts("comp", log_dir) == 3


def test_count_consecutive_reverts_scoped_to_branch(tmp_path):
    log_dir = str(tmp_path)
    log_event("comp", "decision", {}, branch="candidate/a", verdict="revert", log_dir=log_dir)
    log_event("comp", "decision", {}, branch="candidate/b", verdict="revert", log_dir=log_dir)
    log_event("comp", "decision", {}, branch="candidate/b", verdict="revert", log_dir=log_dir)

    assert count_consecutive_reverts("comp", log_dir, branch="candidate/a") == 1
    assert count_consecutive_reverts("comp", log_dir, branch="candidate/b") == 2


def test_count_total_reverts_does_not_reset_after_keep_or_count_diagnostic_signal(tmp_path):
    log_dir = str(tmp_path)
    branch = "candidate/x"
    log_event("comp", "decision", {}, branch=branch, verdict="revert", log_dir=log_dir)
    log_event("comp", "decision", {}, branch=branch, verdict="keep", log_dir=log_dir)
    log_event("comp", "signal_d", {}, branch=branch, log_dir=log_dir)
    log_event("comp", "decision", {}, branch=branch, verdict="revert", log_dir=log_dir)

    assert count_consecutive_reverts("comp", log_dir, branch=branch) == 1
    assert count_total_reverts("comp", log_dir, branch=branch) == 2


@pytest.mark.parametrize(
    "bad_module", ["../escape", "a/b", "a\\b", "..", "/etc/passwd", ""]
)
def test_evaluate_change_rejects_an_unsafe_module_name(tmp_path, bad_module):
    with pytest.raises(gate.CandidateLifecycleError, match="not a single safe path segment"):
        gate.evaluate_change(bad_module, "candidate/x", log_dir=str(tmp_path))


def test_isolated_candidate_rejects_an_unsafe_module_name_before_any_worktree_work(
    tmp_path,
):
    repo = _repo_with_candidate(tmp_path)

    with pytest.raises(gate.CandidateLifecycleError, match="not a single safe path segment"):
        gate.evaluate_isolated_candidate(
            repo, "../escape", "candidate/R-200", authorization=_independent_review(repo)
        )

    assert _git(repo, "worktree", "list", "--porcelain").count("worktree ") == 1


def test_evaluation_gate_logs_negative_patterns_and_enforces_total_attempt_ceiling(
    tmp_path, monkeypatch, capsys
):
    log_dir = str(tmp_path)
    branch = "candidate/R-099"
    monkeypatch.setattr(gate, "run_script", lambda *_args, **_kwargs: (1, "", "failed"))

    code, _ = gate.evaluate_change(
        "comp", branch, log_dir=log_dir, stagnation_limit=5, attempt_ceiling=2
    )
    assert code == gate.REVERT

    # A successful decision resets stagnation but not the branch-wide ceiling.
    log_event("comp", "decision", {}, branch=branch, verdict="keep", log_dir=log_dir)
    code, reason = gate.evaluate_change(
        "comp", branch, log_dir=log_dir, stagnation_limit=5, attempt_ceiling=2
    )

    assert code == gate.ESCALATE
    assert "attempt ceiling" in reason
    assert len(read_negative_patterns("comp", log_dir)) == 2
    assert "[NEGATIVE PATTERNS]" in capsys.readouterr().out


def test_evaluation_gate_promotes_baseline_only_when_explicitly_requested(tmp_path, monkeypatch):
    log_dir = str(tmp_path)
    payload = {"metric": "latency_p99_ms", "value": 42.0, "direction": "lower"}
    script_results = iter([(0, "", ""), (0, json.dumps(payload), "")])
    monkeypatch.setattr(gate, "run_script", lambda *_args, **_kwargs: next(script_results))

    code, _ = gate.evaluate_change("comp", "main", log_dir=log_dir, record_baseline=True)

    assert code == gate.KEEP
    baseline = find_baseline("comp", "latency_p99_ms", log_dir)
    assert baseline["branch"] == "main"
    assert baseline["metrics"]["value"] == 42.0


def test_bash_prefers_git_installation_over_windows_wsl_shim(monkeypatch):
    git = r"C:\Program Files\Git\cmd\git.exe"
    git_bash = r"C:\Program Files\Git\bin\bash.exe"

    monkeypatch.delenv("RECURSPEC_BASH", raising=False)
    monkeypatch.setattr(
        gate.shutil,
        "which",
        lambda command: git if command == "git" else r"C:\Windows\System32\bash.exe",
    )
    monkeypatch.setattr(gate.os.path, "isfile", lambda path: path == git_bash)

    assert gate._bash(platform="nt") == git_bash


def test_comparison_exposes_merge_blocking_verdicts():
    assert compare("latency_ms", 200, 100, tolerance_pct=20).blocks_merge is True
    assert compare("latency_ms", 101, 100, tolerance_pct=20).blocks_merge is False


def test_run_script_exports_the_running_interpreter(tmp_path, monkeypatch):
    captured: dict[str, str] = {}

    def fake_run(args, capture_output=True, text=True, timeout=300, cwd=None, env=None):
        captured.update(env or {})

        class Result:
            returncode = 0
            stdout = ""
            stderr = ""

        return Result()

    script = tmp_path / "probe.sh"
    script.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    monkeypatch.setattr(gate.subprocess, "run", fake_run)
    monkeypatch.setattr(gate, "_bash", lambda: "bash")

    code, _out, _err = gate.run_script(str(script), "checkout", cwd=tmp_path)

    assert code == 0
    assert captured["RECURSPEC_PYTHON"] == sys.executable


def test_run_script_reports_a_missing_probe(tmp_path):
    code, stdout, stderr = gate.run_script(str(tmp_path / "missing.sh"), "checkout")

    assert code == 127
    assert stdout == ""
    assert "Script not found" in stderr


def test_evaluation_gate_reverts_unparseable_measurement(tmp_path, monkeypatch):
    script_results = iter([(0, "", ""), (0, "not-json", "")])
    monkeypatch.setattr(gate, "run_script", lambda *_args, **_kwargs: next(script_results))

    code, reason = gate.evaluate_change("checkout", "candidate/R-100", log_dir=str(tmp_path))

    assert code == gate.REVERT
    assert reason == "unparseable measurement"
    assert read_negative_patterns("checkout", str(tmp_path))[-1]["branch"] == "candidate/R-100"


def test_evaluation_gate_reverts_a_tiered_regression(tmp_path, monkeypatch):
    log_dir = str(tmp_path)
    log_event(
        "checkout",
        "baseline",
        {"metric": "latency_p99_ms", "value": 100.0},
        branch="main",
        log_dir=log_dir,
    )
    payload = {
        "status": "success",
        "metrics": [
            {
                "metric": "latency_p99_ms",
                "value": 150.0,
                "direction": "lower",
                "tier": "hard_gate",
            }
        ],
    }
    script_results = iter([(0, "", ""), (0, json.dumps(payload), "")])
    monkeypatch.setattr(gate, "run_script", lambda *_args, **_kwargs: next(script_results))

    code, reason = gate.evaluate_change(
        "checkout", "candidate/R-101", log_dir=log_dir, tolerance_pct=20
    )

    assert code == gate.REVERT
    assert reason == "HARD GATE regressed/unknown: latency_p99_ms"
    assert any(event["event_type"] == "signal_d" for event in read_events("checkout", log_dir))


def test_isolated_candidate_keep_fast_forwards_baseline_and_disposes_worktree(
    tmp_path, monkeypatch
):
    repo = _repo_with_candidate(tmp_path)
    calls = []

    def evaluate(module, branch, **kwargs):
        calls.append((module, branch, kwargs))
        work_dir = Path(kwargs["work_dir"])
        assert work_dir != repo
        assert (work_dir / "state.txt").read_text(encoding="utf-8") == "candidate\n"
        return gate.KEEP, "checks and metrics passed"

    monkeypatch.setattr(gate, "evaluate_change", evaluate)

    code, reason = gate.evaluate_isolated_candidate(
        repo,
        "checkout",
        "candidate/R-200",
        baseline_branch="main",
        authorization=_independent_review(repo),
    )

    assert (code, reason) == (gate.KEEP, "checks and metrics passed")
    assert (repo / "state.txt").read_text(encoding="utf-8") == "candidate\n"
    assert _git(repo, "branch", "--show-current") == "main"
    assert _git(repo, "worktree", "list", "--porcelain").count("worktree ") == 1
    assert Path(calls[0][2]["log_dir"]) == repo / ".recurspec" / "evidence"
    assert calls[0][2]["record_baseline"] is False
    authorization = [
        event
        for event in read_events("checkout", str(repo / ".recurspec" / "evidence"))
        if event["event_type"] == "merge_authorization"
    ]
    assert authorization[-1]["metrics"] == {
        "maker_id": "worker-1",
        "checker_id": "worker-2",
    }
    assert authorization[-1]["evidence_stage"] == "Observed"


def test_isolated_candidate_revert_leaves_baseline_unchanged_and_disposes_worktree(
    tmp_path, monkeypatch
):
    repo = _repo_with_candidate(tmp_path)
    monkeypatch.setattr(
        gate,
        "evaluate_change",
        lambda *_args, **_kwargs: (gate.REVERT, "correctness failed"),
    )

    code, reason = gate.evaluate_isolated_candidate(
        repo, "checkout", "candidate/R-200", authorization=_independent_review(repo)
    )

    assert (code, reason) == (gate.REVERT, "correctness failed")
    assert (repo / "state.txt").read_text(encoding="utf-8") == "baseline\n"
    assert _git(repo, "worktree", "list", "--porcelain").count("worktree ") == 1


def test_isolated_candidate_refuses_probe_mutations_instead_of_merging_an_unevaluated_tree(
    tmp_path, monkeypatch
):
    repo = _repo_with_candidate(tmp_path)

    def mutating_evaluator(_module, _branch, **kwargs):
        worktree = Path(kwargs["work_dir"])
        (worktree / "state.txt").write_text("mutated by probe\n", encoding="utf-8")
        (worktree / "untracked.txt").write_text("also dirty\n", encoding="utf-8")
        return gate.KEEP, "passed against dirty state"

    monkeypatch.setattr(gate, "evaluate_change", mutating_evaluator)

    with pytest.raises(gate.CandidateLifecycleError, match="modified the Candidate worktree"):
        gate.evaluate_isolated_candidate(
            repo, "checkout", "candidate/R-200", authorization=_independent_review(repo)
        )

    assert (repo / "state.txt").read_text(encoding="utf-8") == "baseline\n"
    assert _git(repo, "worktree", "list", "--porcelain").count("worktree ") == 1


def test_isolated_candidate_evaluates_against_trusted_probes_not_the_candidates_own(
    tmp_path: Path,
):
    if gate._bash() is None:
        pytest.skip("no POSIX shell available to run real probes")
    repo = _repo_with_candidate(tmp_path)
    _git(repo, "switch", "candidate/R-200")
    (repo / "state.txt").write_text("broken\n", encoding="utf-8")
    (repo / "modules" / "checkout" / "checks.sh").write_text(
        "#!/usr/bin/env bash\nexit 0\n", encoding="utf-8"
    )
    _git(repo, "add", "state.txt", "modules")
    _git(repo, "commit", "-m", "weaken checks.sh and break state")
    _git(repo, "switch", "main")

    code, reason = gate.evaluate_isolated_candidate(
        repo, "checkout", "candidate/R-200", authorization=_independent_review(repo)
    )

    assert code == gate.REVERT
    assert "checks.sh failed" in reason
    assert (repo / "state.txt").read_text(encoding="utf-8") == "baseline\n"


def test_isolated_candidate_evaluates_against_trusted_tests_dependency_not_the_candidates_own(
    tmp_path: Path,
):
    """checks.sh is pinned to the trusted baseline, but every bundled checks.sh in this
    repository also shells out to files under tests/ - a Candidate that weakens what
    checks.sh itself calls into must not bypass correctness backpressure either (R-600)."""
    if gate._bash() is None:
        pytest.skip("no POSIX shell available to run real probes")
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-b", "main", str(repo)], check=True, capture_output=True)
    _git(repo, "config", "user.email", "tests@example.invalid")
    _git(repo, "config", "user.name", "Recurspec Tests")
    (repo / "state.txt").write_text("baseline\n", encoding="utf-8")
    (repo / "tests").mkdir()
    (repo / "tests" / "assertions.sh").write_text(
        "if grep -q broken \"${DIR}/state.txt\" 2>/dev/null; then\n"
        '  echo "state is broken" >&2\n'
        "  exit 1\n"
        "fi\n"
        "exit 0\n",
        encoding="utf-8",
    )
    modules = repo / "modules" / "checkout"
    modules.mkdir(parents=True)
    (modules / "checks.sh").write_text(
        "#!/usr/bin/env bash\n"
        "set -euo pipefail\n"
        'DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"\n'
        'source "${DIR}/tests/assertions.sh"\n',
        encoding="utf-8",
    )
    (modules / "measure.sh").write_text(_TRUSTED_MEASURE_SH, encoding="utf-8")
    _git(repo, "add", "state.txt", "tests", "modules")
    _git(repo, "commit", "-m", "baseline")
    _git(repo, "switch", "-c", "candidate/R-200")
    (repo / "state.txt").write_text("broken\n", encoding="utf-8")
    (repo / "tests" / "assertions.sh").write_text("exit 0\n", encoding="utf-8")
    _git(repo, "add", "state.txt", "tests")
    _git(repo, "commit", "-m", "break state and weaken the checks.sh dependency")
    _git(repo, "switch", "main")

    code, reason = gate.evaluate_isolated_candidate(
        repo, "checkout", "candidate/R-200", authorization=_independent_review(repo)
    )

    assert code == gate.REVERT
    assert "checks.sh failed" in reason
    assert (repo / "state.txt").read_text(encoding="utf-8") == "baseline\n"


def test_isolated_candidate_evaluates_against_trusted_module_helpers_not_the_candidates_own(
    tmp_path: Path,
):
    """Pinning checks.sh is not enough if it sources a sibling helper under modules/
    that a Candidate can weaken (R-621)."""
    if gate._bash() is None:
        pytest.skip("no POSIX shell available to run real probes")
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-b", "main", str(repo)], check=True, capture_output=True)
    _git(repo, "config", "user.email", "tests@example.invalid")
    _git(repo, "config", "user.name", "Recurspec Tests")
    (repo / "state.txt").write_text("baseline\n", encoding="utf-8")
    modules = repo / "modules" / "checkout"
    modules.mkdir(parents=True)
    (modules / "lib.sh").write_text(
        "if grep -q broken \"${DIR}/state.txt\" 2>/dev/null; then\n"
        '  echo "state is broken" >&2\n'
        "  exit 1\n"
        "fi\n"
        "exit 0\n",
        encoding="utf-8",
    )
    (modules / "checks.sh").write_text(
        "#!/usr/bin/env bash\n"
        "set -euo pipefail\n"
        'DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"\n'
        'source "${DIR}/modules/checkout/lib.sh"\n',
        encoding="utf-8",
    )
    (modules / "measure.sh").write_text(_TRUSTED_MEASURE_SH, encoding="utf-8")
    _git(repo, "add", "state.txt", "modules")
    _git(repo, "commit", "-m", "baseline")
    _git(repo, "switch", "-c", "candidate/R-200")
    (repo / "state.txt").write_text("broken\n", encoding="utf-8")
    (modules / "lib.sh").write_text("exit 0\n", encoding="utf-8")
    _git(repo, "add", "state.txt", "modules")
    _git(repo, "commit", "-m", "break state and weaken the modules helper")
    _git(repo, "switch", "main")

    code, reason = gate.evaluate_isolated_candidate(
        repo, "checkout", "candidate/R-200", authorization=_independent_review(repo)
    )

    assert code == gate.REVERT
    assert "checks.sh failed" in reason


def test_isolated_candidate_evaluates_against_a_manifest_declared_trusted_helper(
    tmp_path: Path,
):
    """A project can pin a probe-adjacent helper the fixed lists cannot anticipate (e.g.
    a plugin config or a scripts/ tree outside the hard-coded set) via
    .recurspec/trusted-inputs.json; a Candidate must not be able to weaken it either
    (R-640)."""
    if gate._bash() is None:
        pytest.skip("no POSIX shell available to run real probes")
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-b", "main", str(repo)], check=True, capture_output=True)
    _git(repo, "config", "user.email", "tests@example.invalid")
    _git(repo, "config", "user.name", "Recurspec Tests")
    (repo / "state.txt").write_text("baseline\n", encoding="utf-8")
    (repo / ".recurspec").mkdir()
    (repo / ".recurspec" / "trusted-inputs.json").write_text(
        json.dumps({"paths": ["helpers"]}), encoding="utf-8"
    )
    helpers = repo / "helpers"
    helpers.mkdir()
    (helpers / "lib.sh").write_text(
        "if grep -q broken \"${DIR}/state.txt\" 2>/dev/null; then\n"
        '  echo "state is broken" >&2\n'
        "  exit 1\n"
        "fi\n"
        "exit 0\n",
        encoding="utf-8",
    )
    modules = repo / "modules" / "checkout"
    modules.mkdir(parents=True)
    (modules / "checks.sh").write_text(
        "#!/usr/bin/env bash\n"
        "set -euo pipefail\n"
        'DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"\n'
        'source "${DIR}/helpers/lib.sh"\n',
        encoding="utf-8",
    )
    (modules / "measure.sh").write_text(_TRUSTED_MEASURE_SH, encoding="utf-8")
    _git(repo, "add", "state.txt", "modules", "helpers", ".recurspec")
    _git(repo, "commit", "-m", "baseline")
    _git(repo, "switch", "-c", "candidate/R-200")
    (repo / "state.txt").write_text("broken\n", encoding="utf-8")
    (helpers / "lib.sh").write_text("exit 0\n", encoding="utf-8")
    _git(repo, "add", "state.txt", "helpers")
    _git(repo, "commit", "-m", "break state and weaken the manifest-trusted helper")
    _git(repo, "switch", "main")

    code, reason = gate.evaluate_isolated_candidate(
        repo, "checkout", "candidate/R-200", authorization=_independent_review(repo)
    )

    assert code == gate.REVERT
    assert "checks.sh failed" in reason


def test_load_trusted_manifest_is_absent_by_default(tmp_path: Path):
    assert gate._load_trusted_manifest(tmp_path) == ()


@pytest.mark.parametrize(
    "payload",
    [
        "not json",
        "{}",
        '{"paths": "helpers"}',
        '{"paths": [1]}',
    ],
)
def test_load_trusted_manifest_fails_closed_on_malformed_content(tmp_path: Path, payload: str):
    (tmp_path / ".recurspec").mkdir()
    (tmp_path / ".recurspec" / "trusted-inputs.json").write_text(payload, encoding="utf-8")

    with pytest.raises(gate.CandidateLifecycleError):
        gate._load_trusted_manifest(tmp_path)


@pytest.mark.parametrize(
    "entry",
    ["../outside", "/etc/passwd", "C:\\Windows", "a/../b", "", "  helpers", "~/x"],
)
def test_load_trusted_manifest_refuses_a_path_that_escapes_the_repository(
    tmp_path: Path, entry: str
):
    (tmp_path / ".recurspec").mkdir()
    (tmp_path / ".recurspec" / "trusted-inputs.json").write_text(
        json.dumps({"paths": [entry]}), encoding="utf-8"
    )

    with pytest.raises(gate.CandidateLifecycleError):
        gate._load_trusted_manifest(tmp_path)


def test_isolated_candidate_refuses_a_module_without_trusted_baseline_probes(tmp_path: Path):
    repo = _repo_with_candidate(tmp_path)

    with pytest.raises(gate.CandidateLifecycleError, match="no trusted baseline probe"):
        gate.evaluate_isolated_candidate(
            repo, "does-not-exist", "candidate/R-200", authorization=_independent_review(repo)
        )


def test_isolated_candidate_promotes_baseline_only_after_merge(tmp_path, monkeypatch):
    repo = _repo_with_candidate(tmp_path)
    calls = []

    def evaluate(module, branch, **kwargs):
        calls.append((branch, kwargs))
        return gate.KEEP, "passed"

    monkeypatch.setattr(gate, "evaluate_change", evaluate)

    code, _ = gate.evaluate_isolated_candidate(
        repo,
        "checkout",
        "candidate/R-200",
        baseline_branch="main",
        record_baseline=True,
        authorization=_independent_review(repo),
    )

    assert code == gate.KEEP
    assert [branch for branch, _ in calls] == ["candidate/R-200", "main"]
    assert calls[0][1]["record_baseline"] is False
    assert calls[1][1]["record_baseline"] is True
    assert Path(calls[1][1]["work_dir"]) == repo
    assert (repo / "state.txt").read_text(encoding="utf-8") == "candidate\n"


def test_isolated_candidate_disposes_worktree_when_evaluation_crashes(tmp_path, monkeypatch):
    repo = _repo_with_candidate(tmp_path)

    def broken_evaluator(*_args, **_kwargs):
        raise RuntimeError("instrument crashed")

    monkeypatch.setattr(gate, "evaluate_change", broken_evaluator)

    with pytest.raises(RuntimeError, match="instrument crashed"):
        gate.evaluate_isolated_candidate(
            repo, "checkout", "candidate/R-200", authorization=_independent_review(repo)
        )

    assert _git(repo, "worktree", "list", "--porcelain").count("worktree ") == 1


def test_isolated_candidate_prunes_stale_registration_before_creating_worktree(
    tmp_path, monkeypatch
):
    repo = _repo_with_candidate(tmp_path)
    stale = tmp_path / "stale-worktree"
    _git(repo, "worktree", "add", str(stale), "candidate/R-200")
    shutil.rmtree(stale)
    monkeypatch.setattr(
        gate,
        "evaluate_change",
        lambda *_args, **_kwargs: (gate.REVERT, "expected rejection"),
    )

    code, reason = gate.evaluate_isolated_candidate(
        repo, "checkout", "candidate/R-200", authorization=_independent_review(repo)
    )

    assert (code, reason) == (gate.REVERT, "expected rejection")
    assert _git(repo, "worktree", "list", "--porcelain").count("worktree ") == 1


def test_isolated_candidate_prunes_metadata_when_worktree_directory_disappears(
    tmp_path, monkeypatch
):
    repo = _repo_with_candidate(tmp_path)

    def evaluator_that_loses_worktree(_module, _branch, **kwargs):
        shutil.rmtree(kwargs["work_dir"])
        return gate.REVERT, "instrument removed its worktree"

    monkeypatch.setattr(gate, "evaluate_change", evaluator_that_loses_worktree)

    code, reason = gate.evaluate_isolated_candidate(
        repo, "checkout", "candidate/R-200", authorization=_independent_review(repo)
    )

    assert (code, reason) == (gate.REVERT, "instrument removed its worktree")
    assert _git(repo, "worktree", "list", "--porcelain").count("worktree ") == 1


def test_isolated_candidate_ignores_recurspec_runtime_state_when_checking_cleanliness(
    tmp_path, monkeypatch
):
    repo = _repo_with_candidate(tmp_path)
    # An untracked worker-authorizations.json and evidence log at the documented paths
    # must not themselves block evaluation, even if .gitignore hasn't caught up (R-604).
    (repo / ".recurspec" / "evidence" / "checkout").mkdir(parents=True)
    (repo / ".recurspec" / "evidence" / "checkout" / "log.jsonl").write_text(
        "{}\n", encoding="utf-8"
    )
    (repo / ".recurspec" / "worker-authorizations.json").write_text("{}", encoding="utf-8")
    monkeypatch.setattr(
        gate, "evaluate_change", lambda *_args, **_kwargs: (gate.KEEP, "passed")
    )

    code, _ = gate.evaluate_isolated_candidate(
        repo, "checkout", "candidate/R-200", authorization=_independent_review(repo)
    )

    assert code == gate.KEEP


def test_isolated_candidate_still_refuses_a_tracked_dirty_file_under_recurspec(
    tmp_path, monkeypatch
):
    """A project that deliberately commits something under .recurspec/ (e.g. a checked-in
    config) must still block evaluation if that tracked file is dirty - R-604 only
    excludes Recurspec's own *untracked, generated* runtime state, never a blanket
    exclusion of the whole directory (which would also hide this)."""
    repo = _repo_with_candidate(tmp_path)
    (repo / ".recurspec").mkdir()
    (repo / ".recurspec" / "config.json").write_text('{"tracked": true}', encoding="utf-8")
    _git(repo, "add", ".recurspec/config.json")
    _git(repo, "commit", "-m", "track a .recurspec config on purpose")
    (repo / ".recurspec" / "config.json").write_text('{"tracked": false}', encoding="utf-8")
    monkeypatch.setattr(
        gate,
        "evaluate_change",
        lambda *_args, **_kwargs: pytest.fail(
            "dirty tracked .recurspec file must not be evaluated"
        ),
    )

    with pytest.raises(gate.CandidateLifecycleError, match="clean"):
        gate.evaluate_isolated_candidate(
            repo, "checkout", "candidate/R-200", authorization=_independent_review(repo)
        )


def test_isolated_candidate_refuses_a_dirty_or_wrong_baseline(tmp_path, monkeypatch):
    repo = _repo_with_candidate(tmp_path)
    (repo / "state.txt").write_text("do not merge over me\n", encoding="utf-8")
    monkeypatch.setattr(
        gate,
        "evaluate_change",
        lambda *_args, **_kwargs: pytest.fail("dirty baseline must not be evaluated"),
    )

    with pytest.raises(gate.CandidateLifecycleError, match="clean"):
        gate.evaluate_isolated_candidate(
            repo, "checkout", "candidate/R-200", authorization=_independent_review(repo)
        )

    (repo / "state.txt").write_text("baseline\n", encoding="utf-8")
    _git(repo, "switch", "candidate/R-200")
    with pytest.raises(gate.CandidateLifecycleError, match="checked out"):
        gate.evaluate_isolated_candidate(
            repo, "checkout", "candidate/R-200", authorization=_independent_review(repo)
        )


def test_worker_pool_cannot_issue_merge_authorization_to_the_maker():
    pool = WorkerPool(lambda *_args: RuntimeResponse({}, 1, 1, 1.0), concurrency=1)
    pool.dispatch("R-200", {}, "frame", "worker-1", 100)

    refused = pool.dispatch(
        "R-200", {}, "check", "worker-1", 100, "candidate/R-200", "abc123"
    )

    assert refused.outcome == "refused"
    with pytest.raises(ValueError, match="no completed maker/checker authorization"):
        pool.merge_authorization("R-200")


def test_isolated_candidate_refuses_worker_authorization_for_another_candidate(tmp_path):
    repo = _repo_with_candidate(tmp_path)
    pool = WorkerPool(lambda *_args: RuntimeResponse({"approved": True}, 1, 1, 1.0), concurrency=1)
    pool.dispatch("R-999", {}, "frame", "worker-1", 100)
    pool.dispatch("R-999", {}, "check", "worker-2", 100, "candidate/R-999", "abc123")

    with pytest.raises(gate.CandidateLifecycleError, match="does not match"):
        gate.evaluate_isolated_candidate(
            repo,
            "checkout",
            "candidate/R-200",
            authorization=pool.merge_authorization("R-999"),
        )


def test_implementor_bks_metrics_only_omits_source_even_when_files_are_named(tmp_path):
    from recurspec.metrics import implementor_bks

    log_dir = tmp_path / "evidence"
    source = tmp_path / "winner.py"
    source.write_text("def leaked():\n    return 1\n", encoding="utf-8")
    log_event(
        "checkout",
        "baseline",
        {"metric": "latency", "value": 12.0, "direction": "lower", "tier": "target"},
        branch="main",
        log_dir=str(log_dir),
    )

    hidden = implementor_bks(
        "checkout",
        log_dir=str(log_dir),
        metrics_only=True,
        source_files=[str(source)],
    )
    shown = implementor_bks(
        "checkout",
        log_dir=str(log_dir),
        metrics_only=False,
        source_files=[str(source)],
    )

    assert hidden.metrics_only is True
    assert hidden.source_excerpts == ()
    assert hidden.metrics[0]["metric"] == "latency"
    assert hidden.metrics[0]["value"] == 12.0
    assert "leaked" not in json.dumps(hidden.as_dict())
    assert shown.source_excerpts[0][1].startswith("def leaked")


def test_predict_from_negative_patterns_refuses_without_evidence(tmp_path):
    from recurspec.metrics import PredictorError, predict_from_negative_patterns

    with pytest.raises(PredictorError, match="refuse to invent"):
        predict_from_negative_patterns("checkout", log_dir=str(tmp_path / "empty"))

    log_dir = tmp_path / "evidence"
    log_event(
        "checkout",
        "negative_pattern",
        {},
        reason="retry the same patch",
        verdict="REVERT",
        log_dir=str(log_dir),
    )
    log_event(
        "checkout",
        "negative_pattern",
        {},
        reason="retry the same patch",
        verdict="REVERT",
        log_dir=str(log_dir),
    )
    rows = predict_from_negative_patterns("checkout", log_dir=str(log_dir))
    assert rows == [{"count": 2, "reason": "retry the same patch"}]
