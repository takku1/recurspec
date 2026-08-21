#!/usr/bin/env bash
set -euo pipefail

# shellcheck source=../_probe_prelude.sh
. "$(dirname "${BASH_SOURCE[0]}")/../_probe_prelude.sh"

"${PYTHON}" -m pytest tests/test_job_store.py -q
"${PYTHON}" -m ruff check src tests
