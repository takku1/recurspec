#!/usr/bin/env bash
# Correctness probe template. It deliberately refuses until assertions replace it.
set -euo pipefail

MODULE_NAME="${1:-MODULE_NAME}"
echo "replace examples/module/checks.sh with real ${MODULE_NAME} assertions" >&2
echo "a placeholder correctness probe cannot authorize KEEP" >&2
exit 2
