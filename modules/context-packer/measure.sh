#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && (pwd -W 2>/dev/null || pwd))"
cd "${REPO_ROOT}"
export PYTHONPATH="${REPO_ROOT}/src${PYTHONPATH:+:${PYTHONPATH}}"

# Some systems only ship python3, not a bare "python" alias; a bundled probe must
# not silently assume the maintainer's own dev environment shape (R-606).
PYTHON="${RECURSPEC_PYTHON:-$(command -v python3 2>/dev/null || command -v python 2>/dev/null || true)}"
if [ -z "${PYTHON}" ]; then
  echo "no python3 or python interpreter found on PATH" >&2
  exit 127
fi

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
