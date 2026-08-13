#!/usr/bin/env bash
# Measurement probe template
# Output: Structured JSON to stdout with exit code 0
set -euo pipefail

MODULE_NAME="${1:-MODULE_NAME}"
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

# --- MEASUREMENT PROTOCOL ---
# Perform hardware/module measurement pass here.
# Measure across input shapes / iterations to record variance.

# Dummy measurement placeholder — replace with actual execution
RUN_LATENCY_MS=42.5

# Emit the Recurspec measurement payload as the final JSON object on stdout.
#
# `direction` tells the keep/revert gate which way is better. Omit it only when
# the metric name makes it obvious (see src/recurspec/metrics.py); an undecidable
# direction blocks the merge rather than being guessed.
#
# `status` and `evidence_stage` are checked for self-contradiction: reporting
# success without a numeric value, or claiming a stage above Measured, marks
# the instrument broken and reverts the branch.
cat <<EOF
{
  "ts": "${TIMESTAMP}",
  "event_type": "measurement",
  "module": "${MODULE_NAME}",
  "metric": "latency_p99_ms",
  "value": ${RUN_LATENCY_MS},
  "unit": "ms",
  "direction": "lower",
  "evidence_stage": "Measured",
  "status": "success"
}
EOF
