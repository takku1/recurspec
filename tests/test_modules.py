"""End-to-end coverage: every bundled measure.sh must parse and emit its declared
metrics (R-606). This would have caught both the missing job-store/worker-pool scripts
and the contract-engine multi-object payload bug."""

from __future__ import annotations

from pathlib import Path

import pytest

from recurspec import evaluation as gate
from recurspec.metrics import parse_measurement

REPO_ROOT = Path(__file__).resolve().parents[1]

EXPECTED_METRICS = {
    "contract-engine": {"valid_fixture_acceptance_rate", "valid_tree_fixture_acceptance_rate"},
    "contract-reconciler": {"seeded_reconciliation_precision"},
    "evaluation-gate": {"evaluation_gate_latency_ms"},
    "job-store": {"rewalk_amplification"},
    "stack-resolver": {"resolution_completeness"},
    "structure-gate": {"gate_false_negative_rate"},
    "worker-pool": {"wall_clock_per_node_p95"},
}


def _metric_names(payload: dict) -> set[str]:
    entries = payload.get("metrics")
    if isinstance(entries, list):
        return {entry["metric"] for entry in entries}
    return {payload["metric"]}


@pytest.mark.parametrize("module", sorted(EXPECTED_METRICS))
def test_bundled_measure_scripts_emit_their_declared_metrics(module):
    if gate._bash() is None:
        pytest.skip("no POSIX shell available to run bundled probes")

    measure_path = Path("modules") / module / "measure.sh"
    assert (REPO_ROOT / measure_path).is_file(), f"{measure_path} is not bundled"

    code, out, err = gate.run_script(str(measure_path), module, cwd=REPO_ROOT, timeout=120)

    assert code == 0, f"{measure_path} exited {code}: {err or out}"
    payload = parse_measurement(out)
    assert _metric_names(payload) == EXPECTED_METRICS[module]


def test_every_declared_module_has_both_probe_scripts():
    for module in EXPECTED_METRICS:
        module_dir = REPO_ROOT / "modules" / module
        assert (module_dir / "checks.sh").is_file(), f"modules/{module}/checks.sh is missing"
        assert (module_dir / "measure.sh").is_file(), f"modules/{module}/measure.sh is missing"
