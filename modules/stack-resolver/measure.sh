#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && (pwd -W 2>/dev/null || pwd))"
cd "${REPO_ROOT}"
export PYTHONPATH="${REPO_ROOT}/src${PYTHONPATH:+:${PYTHONPATH}}"

python - <<'PY'
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
