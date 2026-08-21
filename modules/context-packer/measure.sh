#!/usr/bin/env bash
set -euo pipefail

# shellcheck source=../_probe_prelude.sh
. "$(dirname "${BASH_SOURCE[0]}")/../_probe_prelude.sh"

"${PYTHON}" - <<'PY'
import json
from pathlib import Path

from recurspec.spec_runner.context_packer import Packet, pack

tree = Path("tests/fixtures/contracts/valid-tree")
result = pack("transform/SYSTEM.md", tree, max_tokens_per_node=100_000)
ok = isinstance(result, Packet)
payload = {
    "direction": "lower",
    "evidence_stage": "Sampled",
    "metric": "tokens_per_node_p95",
    "status": "success" if ok else "failure",
    "tier": "observation",
    "unit": "tokens",
    "value": result.estimated_tokens if ok else 0,
}
print(json.dumps(payload, separators=(",", ":"), sort_keys=True))
raise SystemExit(0 if ok else 1)
PY
