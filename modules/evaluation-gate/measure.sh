#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "${REPO_ROOT}"

# Some systems only ship python3, not a bare "python" alias; a bundled probe must
# not silently assume the maintainer's own dev environment shape (R-606).
PYTHON="$(command -v python3 2>/dev/null || command -v python 2>/dev/null || true)"
if [ -z "${PYTHON}" ]; then
  echo "no python3 or python interpreter found on PATH" >&2
  exit 127
fi

START_NS="$(date +%s%N)"
"${PYTHON}" -m pytest tests/test_evaluation.py -q >&2
END_NS="$(date +%s%N)"
LATENCY_MS="$(( (END_NS - START_NS) / 1000000 ))"

printf '{"metric":"evaluation_gate_latency_ms","value":%s,"unit":"ms","direction":"lower","tier":"target","evidence_stage":"Measured","status":"success"}\n' "${LATENCY_MS}"
