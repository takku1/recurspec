#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && (pwd -W 2>/dev/null || pwd))"
cd "${REPO_ROOT}"
export PYTHONPATH="${REPO_ROOT}/src${PYTHONPATH:+:${PYTHONPATH}}"

# Some systems only ship python3, not a bare "python" alias; a bundled probe must
# not silently assume the maintainer's own dev environment shape.
PYTHON="${RECURSPEC_PYTHON:-$(command -v python3 2>/dev/null || command -v python 2>/dev/null || true)}"
if [ -z "${PYTHON}" ]; then
  echo "no python3 or python interpreter found on PATH" >&2
  exit 127
fi

"${PYTHON}" - <<'PY'
import json

from recurspec.technology_resolver import audit_resolutions

audit = audit_resolutions(".")
payload = {
    "direction": "higher",
    "evidence_stage": "Sampled",
    "metric": "resolution_completeness",
    "status": "success" if audit.completeness == 1.0 else "failure",
    "tier": "hard_gate",
    "unit": "ratio",
    "value": audit.completeness,
}
print(json.dumps(payload, separators=(",", ":"), sort_keys=True))
raise SystemExit(0 if audit.valid and audit.completeness == 1.0 else 1)
PY
