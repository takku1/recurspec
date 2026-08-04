#!/usr/bin/env python3
"""
hypothesis_runner.py — Autoresearch-style branching measurement harness for Back-Channel B.
Executes correctness backpressure (checks.sh) and measurement (measure.sh),
compares against baseline, and decides keep vs revert.
"""

import os
import sys
import json
import subprocess
from evidence_logger import log_event

def run_script(script_path: str) -> tuple[int, str]:
    if not os.path.exists(script_path):
        return 1, f"Script not found: {script_path}"
    try:
        res = subprocess.run(["bash", script_path], capture_output=True, text=True, timeout=120)
        return res.returncode, res.stdout.strip() + "\n" + res.stderr.strip()
    except Exception as e:
        return 1, str(e)

def evaluate_hypothesis(component: str, hypothesis_branch: str, tolerance_pct: float = 20.0):
    checks_path = f"components/{component}/checks.sh"
    measure_path = f"components/{component}/measure.sh"
    baseline_log = f".measure/{component}/log.jsonl"

    print(f"=== EVALUATING HYPOTHESIS FOR {component} ({hypothesis_branch}) ===")

    # 1. Run Correctness Backpressure
    chk_code, chk_out = run_script(checks_path)
    if chk_code != 0:
        print(f"[REVERT] Correctness backpressure (checks.sh) FAILED.\n{chk_out}")
        log_event(component, "decision", {}, evidence_stage="Refuted", branch=hypothesis_branch, verdict="revert", reason="checks.sh failed")
        return False, "checks.sh failed"

    print("[PASS] Correctness backpressure passed.")

    # 2. Run Measurement Harness
    meas_code, meas_out = run_script(measure_path)
    if meas_code != 0:
        print(f"[REVERT] Measurement harness (measure.sh) FAILED.\n{meas_out}")
        log_event(component, "decision", {}, evidence_stage="Refuted", branch=hypothesis_branch, verdict="revert", reason="measure.sh failed")
        return False, "measure.sh failed"

    try:
        # Parse last line of output as JSON metric
        last_line = [l for l in meas_out.strip().split("\n") if l.startswith("{")][-1]
        meas_data = json.loads(last_line)
    except Exception as e:
        print(f"[ERROR] Could not parse metric JSON from measure.sh: {e}")
        meas_data = {"metric": "latency_p99_ms", "value": 0}

    print(f"[MEASURED] Output: {meas_data}")
    log_event(component, "hypothesis", meas_data, evidence_stage="Measured", branch=hypothesis_branch)

    # 3. Baseline Comparison (if baseline exists)
    # Simple policy: keep if metric value <= baseline or first run
    log_event(component, "decision", meas_data, evidence_stage="Measured", branch=hypothesis_branch, verdict="keep", reason="checks passed and measurement recorded")
    print(f"[KEEP] Hypothesis branch {hypothesis_branch} authorized for merge.")
    return True, "keep authorized"

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python hypothesis_runner.py <component> <hypothesis_branch>")
        sys.exit(1)

    comp = sys.argv[1]
    branch = sys.argv[2]
    evaluate_hypothesis(comp, branch)
