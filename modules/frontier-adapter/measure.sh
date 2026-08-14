#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && (pwd -W 2>/dev/null || pwd))"
cd "${REPO_ROOT}"
export PYTHONPATH="${REPO_ROOT}/src${PYTHONPATH:+:${PYTHONPATH}}"

PYTHON="${RECURSPEC_PYTHON:-$(command -v python3 2>/dev/null || command -v python 2>/dev/null || true)}"
if [ -z "${PYTHON}" ]; then
  echo "no python3 or python interpreter found on PATH" >&2
  exit 127
fi

"${PYTHON}" - <<'PY'
import json
import tempfile
from pathlib import Path

from recurspec.frontier import FrontierInstrumentError, check_frontiers, publish_frontiers

dest = Path(tempfile.mkdtemp()) / "frontiers"
try:
    publish_frontiers(Path("docs/architecture"), dest)
    check = check_frontiers(dest, Path("."))
    integrity = check.integrity
except FrontierInstrumentError:
    integrity = 0.0

payload = {
    "metric": "ticket_to_leaf_link_integrity",
    "value": integrity,
    "unit": "ratio",
    "direction": "higher",
    "tier": "hard_gate",
    "evidence_stage": "Sampled",
    "status": "success" if integrity == 1.0 else "failure",
}
print(json.dumps(payload, separators=(",", ":"), sort_keys=True))
raise SystemExit(0 if integrity == 1.0 else 1)
PY
