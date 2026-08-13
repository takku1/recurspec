#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
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
raise SystemExit(0 if rate == 1.0 else 1)
PY
