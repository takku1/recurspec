#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && (pwd -W 2>/dev/null || pwd))"
cd "${REPO_ROOT}"
export PYTHONPATH="${REPO_ROOT}/src${PYTHONPATH:+:${PYTHONPATH}}"

python - <<'PY'
import json
import tempfile
from pathlib import Path

from recurspec.structure_gate import check_structure

contract = """# Fixture

## 6. Leaf Execution & Test Seam

- **Implementation:** `src/missing.py`.
- **Tests:** `tests/missing.py`.

## 7. Measurement Seams
"""
expected = {
    "structure.implementation.missing",
    "structure.public.uncontracted",
    "structure.test_surface.missing",
}
with tempfile.TemporaryDirectory() as directory:
    root = Path(directory)
    (root / "src").mkdir()
    node = root / "docs" / "architecture" / "fixture" / "SYSTEM.md"
    node.parent.mkdir(parents=True)
    node.write_text(contract, encoding="utf-8")
    (root / "src" / "orphan.py").write_text("def visible():\n    pass\n", encoding="utf-8")
    detected = {item.code for item in check_structure(root, source_root="src").diagnostics}

misses = len(expected - detected)
rate = misses / len(expected)
payload = {
    "direction": "lower",
    "evidence_stage": "Sampled",
    "metric": "gate_false_negative_rate",
    "status": "success" if rate == 0 else "failure",
    "tier": "hard_gate",
    "unit": "ratio",
    "value": rate,
}
print(json.dumps(payload, separators=(",", ":"), sort_keys=True))
raise SystemExit(0 if rate == 0 else 1)
PY
