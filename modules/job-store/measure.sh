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
import shutil
import tempfile
from pathlib import Path

from recurspec.spec_runner.store import JobStore

with tempfile.TemporaryDirectory() as td:
    root = Path(td)
    tree = root / "tree"
    shutil.copytree(Path("tests/fixtures/contracts/valid-tree"), tree)
    store = JobStore(root / "store.sqlite3")

    store.rebuild_from_tree(tree)
    for node_id in list(store.dirty_nodes()):
        store.clear_dirty(node_id)

    # Change exactly one leaf's contract-hash surface (Section 1); the store's own
    # dirty-propagation invariant also marks its parent, so a correct implementation
    # scores 2 dirtied nodes per 1 actually-changed node - not 1.0, which would mean
    # dirty propagation silently stopped working.
    transform = tree / "transform" / "SYSTEM.md"
    transform.write_text(
        transform.read_text(encoding="utf-8").replace(
            "Transform a source value.", "Transform a source value (measured)."
        ),
        encoding="utf-8",
    )
    store.rebuild_from_tree(tree)
    dirtied = len(store.dirty_nodes())
    changed = 1
    rate = dirtied / changed

payload = {
    "metric": "rewalk_amplification",
    "value": rate,
    "unit": "nodes_dirtied_per_node_changed",
    "direction": "lower",
    "tier": "hard_gate",
    "evidence_stage": "Sampled",
    "status": "success" if dirtied >= changed else "failure",
}
print(json.dumps(payload, separators=(",", ":"), sort_keys=True))
raise SystemExit(0 if dirtied >= changed else 1)
PY
