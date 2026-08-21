#!/usr/bin/env bash
set -euo pipefail

# shellcheck source=../_probe_prelude.sh
. "$(dirname "${BASH_SOURCE[0]}")/../_probe_prelude.sh"

START_NS="$(date +%s%N)"
"${PYTHON}" -m pytest tests/test_evaluation.py -q >&2
END_NS="$(date +%s%N)"
LATENCY_MS="$(( (END_NS - START_NS) / 1000000 ))"

printf '{"metric":"evaluation_gate_latency_ms","value":%s,"unit":"ms","direction":"lower","tier":"target","evidence_stage":"Measured","status":"success"}\n' "${LATENCY_MS}"
