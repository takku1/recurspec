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
    "frontier-adapter": {"ticket_to_leaf_link_integrity"},
    "context-packer": {"tokens_per_node_p95"},
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


def test_bundled_probes_never_invoke_a_bare_python_command():
    """Some systems only ship `python3`, not a bare `python` alias - a probe that shells
    out to `python` directly fails on those systems even though the recurspec package
    itself is installed and importable (R-606). Every bundled script must resolve an
    interpreter (`command -v python3 || command -v python`) before calling it."""
    offenders: list[str] = []
    for script in sorted((REPO_ROOT / "modules").glob("*/*.sh")):
        text = script.read_text(encoding="utf-8")
        if "python" not in text:
            continue
        assert 'command -v python3' in text and 'command -v python' in text, (
            f"{script.relative_to(REPO_ROOT)} calls python without resolving an "
            "interpreter first"
        )
        for line in text.splitlines():
            stripped = line.strip()
            if stripped.startswith("python") and not stripped.startswith("python3"):
                # Only the resolution line itself and comments may start with the bare
                # word "python"; every actual invocation must go through ${PYTHON}.
                if "command -v python" in stripped or stripped.startswith("#"):
                    continue
                offenders.append(f"{script.relative_to(REPO_ROOT)}: {stripped}")

    assert offenders == []


def test_measurement_template_refuses_to_invent_a_default_metric():
    if gate._bash() is None:
        pytest.skip("no POSIX shell available to run the probe template")

    template = REPO_ROOT / "examples" / "module" / "measure.sh"
    code, out, err = gate.run_script(str(template), "example", cwd=REPO_ROOT, timeout=30)

    assert code == 2
    assert '"value"' not in out
    assert "replace" in err.lower()


def test_correctness_template_refuses_to_pass_without_assertions():
    if gate._bash() is None:
        pytest.skip("no POSIX shell available to run the probe template")

    template = REPO_ROOT / "examples" / "module" / "checks.sh"
    code, out, err = gate.run_script(str(template), "example", cwd=REPO_ROOT, timeout=30)

    assert code == 2
    assert "pass" not in out.lower()
    assert "replace" in err.lower()
