#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && (pwd -W 2>/dev/null || pwd))"
cd "${REPO_ROOT}"
export PYTHONPATH="${REPO_ROOT}/src${PYTHONPATH:+:${PYTHONPATH}}"

# Some systems only ship python3, not a bare "python" alias; a bundled probe must
# not silently assume the maintainer's own dev environment shape (R-606).
PYTHON="$(command -v python3 2>/dev/null || command -v python 2>/dev/null || true)"
if [ -z "${PYTHON}" ]; then
  echo "no python3 or python interpreter found on PATH" >&2
  exit 127
fi

"${PYTHON}" - <<'PY'
import json
import tempfile
from pathlib import Path

from recurspec.reconcile import plan_reconciliation

with tempfile.TemporaryDirectory() as directory:
    root = Path(directory)
    (root / "src" / "recurspec").mkdir(parents=True)
    (root / "tests").mkdir()
    (root / "docs" / "architecture").mkdir(parents=True)
    (root / "src" / "recurspec" / "orphan.py").write_text(
        "def visible():\n    pass\n", encoding="utf-8"
    )
    (root / "tests" / "test_extra.py").write_text(
        "def test_extra():\n    pass\n", encoding="utf-8"
    )
    actual = {action.kind for action in plan_reconciliation(root).actions}

expected = {"draft_leaf", "test_seam_review"}
precision = len(expected & actual) / len(actual) if actual else None
payload = {
    "direction": "higher",
    "evidence_stage": "Sampled",
    "metric": "seeded_reconciliation_precision",
    "status": "success" if precision == 1.0 and actual == expected else "failure",
    "tier": "hard_gate",
    "unit": "ratio",
    "value": precision,
}
print(json.dumps(payload, separators=(",", ":"), sort_keys=True))
raise SystemExit(0 if precision == 1.0 and actual == expected else 1)
PY
