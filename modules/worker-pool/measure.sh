#!/usr/bin/env bash
set -euo pipefail

# shellcheck source=../_probe_prelude.sh
. "$(dirname "${BASH_SOURCE[0]}")/../_probe_prelude.sh"

"${PYTHON}" - <<'PY'
import json
import time

from recurspec.spec_runner.workers import DispatchJob, RuntimeResponse, WorkerPool

CALLS = 20


def runtime(packet, phase, tier):
    return RuntimeResponse(body="ok", tokens_in=10, tokens_out=10, ms=0.0)


times: list[float] = []


def timed_runtime(packet, phase, tier):
    start = time.perf_counter()
    response = runtime(packet, phase, tier)
    times.append((time.perf_counter() - start) * 1000.0)
    return response


pool = WorkerPool(runtime=timed_runtime, concurrency=4)
jobs = [
    DispatchJob(
        node_id=f"node-{i}",
        packet={},
        phase="frame",
        worker_id=f"worker-{i}",
        max_tokens_per_node=1000,
    )
    for i in range(CALLS)
]
results = pool.dispatch_many(jobs)
ok = sum(1 for result in results if result.outcome == "ok")

times.sort()
index = max(0, int(round(0.95 * (len(times) - 1))))
p95 = times[index]

payload = {
    "metric": "wall_clock_per_node_p95",
    "value": p95,
    "unit": "ms",
    "direction": "lower",
    "tier": "target",
    "evidence_stage": "Sampled",
    "status": "success" if ok == CALLS else "failure",
}
print(json.dumps(payload, separators=(",", ":"), sort_keys=True))
raise SystemExit(0 if ok == CALLS else 1)
PY
