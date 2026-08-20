#!/usr/bin/env bash
# Measurement probe template. It deliberately refuses until replaced with a real probe.
set -euo pipefail

MODULE_NAME="${1:-MODULE_NAME}"

echo "replace examples/module/measure.sh with a real ${MODULE_NAME} measurement probe" >&2
echo "the probe must emit finite observed values; Recurspec never supplies defaults" >&2
exit 2
