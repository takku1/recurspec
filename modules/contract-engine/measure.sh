#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && (pwd -W 2>/dev/null || pwd))"
cd "${REPO_ROOT}"
export PYTHONPATH="${REPO_ROOT}/src${PYTHONPATH:+:${PYTHONPATH}}"

python - <<'PY'
import json
from pathlib import Path

from recurspec.contract import validate_contract

fixtures = Path("tests/fixtures/contracts/valid")
valid_contracts = sorted(fixtures.rglob("SYSTEM.md"))
accepted = sum(validate_contract(path).valid for path in valid_contracts)
rate = accepted / len(valid_contracts) if valid_contracts else None

payload = {
    "direction": "higher",
    "evidence_stage": "Sampled",
    "metric": "valid_fixture_acceptance_rate",
    "status": "success" if rate == 1.0 else "failure",
    "tier": "hard_gate",
    "unit": "ratio",
    "value": rate,
}
print(json.dumps(payload, separators=(",", ":"), sort_keys=True))

tree_fixtures = [Path("tests/fixtures/contracts/valid-tree")]
accepted_trees = sum(validate_contract(path).valid for path in tree_fixtures)
tree_rate = accepted_trees / len(tree_fixtures) if tree_fixtures else None
tree_payload = {
    "direction": "higher",
    "evidence_stage": "Sampled",
    "metric": "valid_tree_fixture_acceptance_rate",
    "status": "success" if tree_rate == 1.0 else "failure",
    "tier": "hard_gate",
    "unit": "ratio",
    "value": tree_rate,
}
print(json.dumps(tree_payload, separators=(",", ":"), sort_keys=True))
raise SystemExit(0 if rate == 1.0 and tree_rate == 1.0 else 1)
PY
