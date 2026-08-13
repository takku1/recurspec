#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "${REPO_ROOT}"

START_NS="$(date +%s%N)"
python -m pytest tests/test_evaluation.py -q >&2
END_NS="$(date +%s%N)"
LATENCY_MS="$(( (END_NS - START_NS) / 1000000 ))"

printf '{"metric":"evaluation_gate_latency_ms","value":%s,"unit":"ms","direction":"lower","tier":"target","evidence_stage":"Measured","status":"success"}\n' "${LATENCY_MS}"
