#!/usr/bin/env python3
"""Behavioral checks for the Recurspec Evaluation Gate."""

from __future__ import annotations

import json
import os

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
        branch="candidate/OW-01",
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
    with open(os.path.join(log_dir, "comp", "log.jsonl"), "a", encoding="utf-8") as f:
        f.write('{"ts": "trunc\n')
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
        branch="candidate/OW-01",
        verdict="revert",
        reason="checks.sh failed",
        log_dir=log_dir,
    )
    log_event(
        "comp",
        "decision",
        {},
        evidence_stage="Measured",
        branch="candidate/OW-01",
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


def test_evaluation_gate_logs_negative_patterns_and_enforces_total_attempt_ceiling(
    tmp_path, monkeypatch, capsys
):
    log_dir = str(tmp_path)
    branch = "candidate/OW-99"
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

    code, _ = gate.evaluate_change("comp", "candidate/OW-98", log_dir=log_dir, record_baseline=True)

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


def test_run_script_reports_a_missing_probe(tmp_path):
    code, stdout, stderr = gate.run_script(str(tmp_path / "missing.sh"), "checkout")

    assert code == 127
    assert stdout == ""
    assert "Script not found" in stderr


def test_evaluation_gate_reverts_unparseable_measurement(tmp_path, monkeypatch):
    script_results = iter([(0, "", ""), (0, "not-json", "")])
    monkeypatch.setattr(gate, "run_script", lambda *_args, **_kwargs: next(script_results))

    code, reason = gate.evaluate_change("checkout", "candidate/OW-100", log_dir=str(tmp_path))

    assert code == gate.REVERT
    assert reason == "unparseable measurement"
    assert read_negative_patterns("checkout", str(tmp_path))[-1]["branch"] == "candidate/OW-100"


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
        "checkout", "candidate/OW-101", log_dir=log_dir, tolerance_pct=20
    )

    assert code == gate.REVERT
    assert reason == "HARD GATE regressed/unknown: latency_p99_ms"
    assert any(event["event_type"] == "signal_d" for event in read_events("checkout", log_dir))
