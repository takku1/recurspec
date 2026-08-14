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

from recurspec.contract import validate_contract

fixtures = Path("tests/fixtures/contracts/valid")
valid_contracts = sorted(fixtures.rglob("SYSTEM.md"))
accepted = sum(validate_contract(path).valid for path in valid_contracts)
rate = accepted / len(valid_contracts) if valid_contracts else None

tree_fixtures = [Path("tests/fixtures/contracts/valid-tree")]
accepted_trees = sum(validate_contract(path).valid for path in tree_fixtures)
tree_rate = accepted_trees / len(tree_fixtures) if tree_fixtures else None

# Both readings share one measure.sh run, so they are emitted as a single payload
# using the "metrics" envelope - parse_measurement() only ever recovers the last of
# several separate top-level JSON objects, which silently dropped the first metric.
payload = {
    "status": "success" if rate == 1.0 and tree_rate == 1.0 else "failure",
    "metrics": [
        {
            "metric": "valid_fixture_acceptance_rate",
            "value": rate,
            "unit": "ratio",
            "direction": "higher",
            "tier": "hard_gate",
            "evidence_stage": "Sampled",
        },
        {
            "metric": "valid_tree_fixture_acceptance_rate",
            "value": tree_rate,
            "unit": "ratio",
            "direction": "higher",
            "tier": "hard_gate",
            "evidence_stage": "Sampled",
        },
    ],
}
print(json.dumps(payload, separators=(",", ":"), sort_keys=True))
raise SystemExit(0 if rate == 1.0 and tree_rate == 1.0 else 1)
PY
