#!/usr/bin/env bash
set -euo pipefail

# shellcheck source=../_probe_prelude.sh
. "$(dirname "${BASH_SOURCE[0]}")/../_probe_prelude.sh"

"${PYTHON}" -m pytest tests/test_structure_gate.py tests/test_cli.py -q
"${PYTHON}" -m recurspec structure check . --format json
"${PYTHON}" -m ruff check src tests
