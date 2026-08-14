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

"${PYTHON}" -m pytest tests/test_job_store.py -q
ruff check src tests
