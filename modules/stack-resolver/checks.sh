#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && (pwd -W 2>/dev/null || pwd))"
cd "${REPO_ROOT}"
export PYTHONPATH="${REPO_ROOT}/src${PYTHONPATH:+:${PYTHONPATH}}"

python -m pytest tests/test_technology_resolver.py tests/test_cli.py -q
python -m recurspec stack check . --format json
python -m recurspec structure check . --format json
ruff check src tests
