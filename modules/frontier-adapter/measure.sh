#!/usr/bin/env bash
set -euo pipefail

# shellcheck source=../_probe_prelude.sh
. "$(dirname "${BASH_SOURCE[0]}")/../_probe_prelude.sh"

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
