#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && (pwd -W 2>/dev/null || pwd))"
cd "${REPO_ROOT}"
export PYTHONPATH="${REPO_ROOT}/src${PYTHONPATH:+:${PYTHONPATH}}"

python -m pytest tests/test_contract.py tests/test_cli.py -q
python -m recurspec contract check tests/fixtures/contracts/valid-tree --format json
ruff check src tests
