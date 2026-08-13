#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && (pwd -W 2>/dev/null || pwd))"
cd "${REPO_ROOT}"
export PYTHONPATH="${REPO_ROOT}/src${PYTHONPATH:+:${PYTHONPATH}}"

python -m pytest tests/test_reconcile.py tests/test_structure_gate.py tests/test_cli.py -q
python -m recurspec structure check . --format json
python -m recurspec reconcile plan . --format json
ruff check src tests
