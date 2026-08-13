#!/usr/bin/env python3
"""Pure metric decisions for the Recurspec Evaluation Gate.

The keep rule is:

    keep iff checks pass
         AND no blocking metric regresses beyond tolerance
         AND no telemetry contradiction

This module reads the append-only evidence log, resolves each metric's direction and tier, and
classifies the candidate against the trunk Best Known State.

Epistemic rule (research foundation SS5): when a comparison's direction cannot
be established, this module returns UNKNOWN rather than guessing. An absent
baseline is the explicit first-measurement case and is NEUTRAL until the Outer
Loop separately promotes it. A guessed comparison would manufacture
Measured-grade evidence out of nothing.
"""

from __future__ import annotations

import json
import math
import os
import re
from dataclasses import dataclass
from typing import Any


class EvidenceInstrumentError(RuntimeError):
    """The evidence log is corrupt in a way that cannot be safely skipped."""


# --- Metric direction -------------------------------------------------------
# Explicit `direction` in the measure.sh payload always wins. These patterns are
# the fallback for metrics that do not declare one.

LOWER_IS_BETTER = re.compile(
    r"(latency|duration|_ms$|_ns$|_us$|elapsed|time|cost|error|failure|"
    r"regression|bytes|size|memory|alloc|p50|p95|p99|overhead)",
    re.IGNORECASE,
)
HIGHER_IS_BETTER = re.compile(
    r"(rate|ratio|throughput|ops_per|per_sec|accuracy|precision|recall|"
    r"pass|score|coverage|success|hit|uptime|yield)",
    re.IGNORECASE,
)

IMPROVED = "improved"
NEUTRAL = "neutral"
REGRESSED = "regressed"
UNKNOWN = "unknown"


def resolve_direction(metric: str, declared: str | None = None) -> str | None:
    """Return 'lower' | 'higher' | None (undecidable).

    `declared` comes from the measure.sh JSON payload and is authoritative.
    """
    if declared:
        d = declared.strip().lower()
        if d in ("lower", "lower_is_better", "min", "minimize"):
            return "lower"
        if d in ("higher", "higher_is_better", "max", "maximize"):
            return "higher"
        raise ValueError(f"Unrecognized metric direction {declared!r}; use 'lower' or 'higher'.")

    # A metric can match both families (e.g. 'error_rate' -> lower wins because
    # the subject noun dominates). Check lower first: cost/error/latency nouns
    # are the stronger signal.
    if LOWER_IS_BETTER.search(metric):
        return "lower"
    if HIGHER_IS_BETTER.search(metric):
        return "higher"
    return None


# --- Evidence log access ----------------------------------------------------


def read_events(module: str, log_dir: str = ".recurspec/evidence") -> list[dict[str, Any]]:
    """Read the append-only evidence log.

    Only the file's last line may be silently dropped, as a recoverable truncated
    append (e.g. a crash mid-write). A malformed line anywhere else is real corruption
    of prior history - erasing it could turn a real baseline regression into a false
    "no baseline" first measurement, so it raises ``EvidenceInstrumentError`` instead of
    being skipped.
    """
    path = os.path.join(log_dir, module, "log.jsonl")
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as f:
        raw_lines = f.readlines()
    last_index = len(raw_lines) - 1
    events: list[dict[str, Any]] = []
    for index, raw_line in enumerate(raw_lines):
        line = raw_line.strip()
        if not line:
            continue
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError as exc:
            if index == last_index:
                continue
            raise EvidenceInstrumentError(
                f"{path}:{index + 1}: corrupt evidence event blocks a safe baseline "
                f"lookup: {exc}"
            ) from exc
    return events


def find_baseline(
    module: str,
    metric: str,
    log_dir: str = ".recurspec/evidence",
    baseline_branch: str = "main",
) -> dict[str, Any] | None:
    """Most recent accepted measurement of `metric` on the baseline branch.

    Only events that were actually admitted to the trunk count as baseline:
    a measurement taken on a candidate branch that was later reverted must
    never become the bar the next candidate is judged against.
    """
    candidates = [
        e
        for e in read_events(module, log_dir)
        if e.get("branch") == baseline_branch
        and e.get("event_type") in ("baseline", "measurement")
        and isinstance(e.get("metrics"), dict)
        and e["metrics"].get("metric") == metric
        and _numeric(e["metrics"].get("value")) is not None
    ]
    return candidates[-1] if candidates else None


def _numeric(v: Any) -> float | None:
    if isinstance(v, bool):
        return None
    if isinstance(v, (int, float)):
        f = float(v)
        return f if math.isfinite(f) else None
    return None


# --- Comparison -------------------------------------------------------------


@dataclass
class Comparison:
    verdict: str  # IMPROVED | NEUTRAL | REGRESSED | UNKNOWN
    metric: str
    current: float | None
    baseline: float | None
    delta_pct: float | None
    direction: str | None
    reason: str

    @property
    def blocks_merge(self) -> bool:
        return self.verdict in (REGRESSED, UNKNOWN)


def compare(
    metric: str,
    current: Any,
    baseline: Any,
    tolerance_pct: float = 20.0,
    declared_direction: str | None = None,
    noise_pct: float = 2.0,
) -> Comparison:
    """Classify current vs baseline.

    tolerance_pct: regression beyond this is REGRESSED (Signal D metric drift).
                   Within it, the run is NEUTRAL - acceptable for changes that
                   are not performance work.
    noise_pct:     movement smaller than this in either direction is NEUTRAL.

    ``tolerance_pct``/``noise_pct`` are operator-supplied gate configuration, not
    untrusted Candidate evidence, so an invalid value raises rather than failing closed
    via a comparison verdict.
    """
    if not math.isfinite(tolerance_pct) or tolerance_pct < 0:
        raise ValueError(f"tolerance_pct must be a finite, non-negative number: {tolerance_pct!r}")
    if not math.isfinite(noise_pct) or noise_pct < 0:
        raise ValueError(f"noise_pct must be a finite, non-negative number: {noise_pct!r}")

    cur = _numeric(current)
    if cur is None:
        return Comparison(
            UNKNOWN,
            metric,
            None,
            _numeric(baseline),
            None,
            None,
            f"measure.sh produced no numeric value for {metric!r}",
        )

    base = _numeric(baseline)
    if base is None:
        return Comparison(
            NEUTRAL,
            metric,
            cur,
            None,
            None,
            resolve_direction(metric, declared_direction),
            "no prior baseline; recording first measurement",
        )

    direction = resolve_direction(metric, declared_direction)
    if direction is None:
        return Comparison(
            UNKNOWN,
            metric,
            cur,
            base,
            None,
            None,
            f"cannot resolve whether higher or lower is better for {metric!r}; "
            'declare "direction": "lower"|"higher" in measure.sh output',
        )

    if base == 0:
        # Percentage change is undefined against a zero baseline; fall back to
        # sign comparison only.
        if cur == 0:
            return Comparison(
                NEUTRAL, metric, cur, base, 0.0, direction, "unchanged at zero baseline"
            )
        better = cur < base if direction == "lower" else cur > base
        return Comparison(
            IMPROVED if better else REGRESSED,
            metric,
            cur,
            base,
            None,
            direction,
            "zero baseline; compared by sign only",
        )

    raw_pct = (cur - base) / abs(base) * 100.0
    # Signed so that positive always means "better", whichever way the metric runs.
    improvement_pct = -raw_pct if direction == "lower" else raw_pct

    if abs(improvement_pct) < noise_pct:
        verdict, reason = NEUTRAL, f"within +/-{noise_pct}% noise band"
    elif improvement_pct > 0:
        verdict, reason = IMPROVED, f"improved {improvement_pct:.2f}%"
    elif -improvement_pct > tolerance_pct:
        verdict, reason = (
            REGRESSED,
            (
                f"regressed {-improvement_pct:.2f}% (> {tolerance_pct}% tolerance) - "
                "Signal D metric drift"
            ),
        )
    else:
        verdict, reason = (
            NEUTRAL,
            (f"regressed {-improvement_pct:.2f}% but within {tolerance_pct}% tolerance"),
        )

    return Comparison(verdict, metric, cur, base, improvement_pct, direction, reason)


# --- measure.sh payload parsing --------------------------------------------


def parse_measurement(stdout: str) -> dict[str, Any]:
    """Extract the JSON measurement payload from measure.sh stdout.

    Raises ValueError when no payload can be recovered. It must never invent a
    value: a fabricated metric silently becomes Measured-grade evidence and
    corrupts every later comparison.
    """
    text = stdout.strip()
    if not text:
        raise ValueError("measure.sh produced no output")

    # Whole-stdout parse handles the common case, including pretty-printed JSON.
    try:
        obj = json.loads(text)
        if isinstance(obj, dict):
            return obj
    except json.JSONDecodeError:
        pass

    # Otherwise scan for top-level balanced {...} blocks, so a evaluation gate may
    # emit log lines - or multiple diagnostic JSON objects - before its
    # payload. Only complete depth 0->1->0 spans count as candidates: a
    # payload's own nested objects (e.g. a multi-metric entry) must never be
    # mistaken for the whole payload. Tried last-to-first so a genuine
    # payload emitted after diagnostic objects wins.
    spans: list[tuple[int, int]] = []
    depth = 0
    span_start: int | None = None
    for i, ch in enumerate(text):
        if ch == "{":
            if depth == 0:
                span_start = i
            depth += 1
        elif ch == "}":
            if depth > 0:
                depth -= 1
                if depth == 0 and span_start is not None:
                    spans.append((span_start, i))
                    span_start = None

    for start, end in reversed(spans):
        try:
            obj = json.loads(text[start : end + 1])
        except json.JSONDecodeError:
            continue
        if isinstance(obj, dict) and ("metric" in obj or "metrics" in obj):
            return obj

    raise ValueError(
        "could not parse a JSON measurement payload from measure.sh output; "
        'expected an object with at least {"metric": ..., "value": ...}'
    )


# --- Metric tiers (gauntlet-loop-style dominance) --------------------------
# Adopted from the gauntlet-loop evaluation gate (docs/process/evidence-cycle.md
# "Branching measurement"): every metric in a multi-metric payload is assigned
# exactly one tier. Untiered metrics stay on the pre-existing single-metric
# path (see evaluate_candidate docstring for how the two relate).

HARD_GATE = "hard_gate"
TARGET = "target"
OPTIMIZATION = "optimization"
OBSERVATION = "observation"

TIERS = (HARD_GATE, TARGET, OPTIMIZATION, OBSERVATION)


def resolve_tier(declared: str | None) -> str:
    """Return a canonical tier name. Defaults to HARD_GATE: a metric that
    silently fails open defeats the point of a gate, so looser tiers must be
    declared explicitly rather than assumed.
    """
    if not declared:
        return HARD_GATE
    d = declared.strip().lower().replace("-", "_").replace(" ", "_")
    if d not in TIERS:
        raise ValueError(f"Unrecognized metric tier {declared!r}; use one of {TIERS}")
    return d


@dataclass
class DominanceResult:
    accepted: bool
    reason: str
    blocking: list[str]
    improved: list[str]
    regressed: list[str]


def evaluate_candidate(
    comparisons: list[tuple[str, Comparison, str]],
) -> DominanceResult:
    """Multi-metric keep/revert gate, generalizing compare()'s REGRESSED/UNKNOWN
    rule across tiers.

    `comparisons` is a list of (metric_name, Comparison, tier) triples, tier
    already resolved via resolve_tier().

    Accept iff no HARD_GATE, TARGET, or OPTIMIZATION metric is REGRESSED or
    UNKNOWN. NEUTRAL is accepted at every tier - this mirrors compare()'s
    existing single-metric semantics (a regression within tolerance keeps),
    so it is a non-regression gate, not a strict-improvement gate.
    OBSERVATION metrics are recorded but never block and are never required
    to move.

    This function decides keep vs revert only. Whether a kept candidate is
    dominant enough to replace the recorded trunk baseline (Recurspec's Best Known
    State) is the separate, stronger question `--record-baseline` answers
    explicitly after the Outer Loop merges - see
    docs/process/evidence-cycle.md.
    """
    if not comparisons:
        return DominanceResult(True, "no metrics supplied", [], [], [])

    blocking: list[str] = []
    improved: list[str] = []
    regressed: list[str] = []

    for name, cmp_, tier in comparisons:
        if tier == OBSERVATION:
            continue
        if cmp_.verdict in (REGRESSED, UNKNOWN):
            (blocking if tier == HARD_GATE else regressed).append(name)
        elif cmp_.verdict == IMPROVED:
            improved.append(name)

    if blocking:
        return DominanceResult(
            False,
            f"HARD GATE regressed/unknown: {', '.join(blocking)}",
            blocking,
            improved,
            regressed,
        )
    if regressed:
        return DominanceResult(
            False,
            f"TARGET/OPTIMIZATION regressed/unknown: {', '.join(regressed)}",
            blocking,
            improved,
            regressed,
        )
    if improved:
        return DominanceResult(
            True,
            f"dominant: {', '.join(improved)} improved, none regressed",
            blocking,
            improved,
            regressed,
        )
    return DominanceResult(
        True, "no regression at any tier (neutral)", blocking, improved, regressed
    )


# --- Negative-memory buffer --------------------------------------------------
# Adopted from gauntlet-loop: without a record of what failed, an agent
# re-proposes reverted approaches indefinitely. Every REVERT that
# evaluation logs also writes a `negative_pattern` event; a repair
# pass must read this buffer before proposing another change (see
# the Recurspec skill).


def read_negative_patterns(
    module: str, log_dir: str = ".recurspec/evidence"
) -> list[dict[str, Any]]:
    """All negative_pattern events recorded for a module, oldest first."""
    return [e for e in read_events(module, log_dir) if e.get("event_type") == "negative_pattern"]


# --- Escalation boundaries ---------------------------------------------------
# Adopted from gauntlet-loop: bounded attempts stop an agent from burning
# budget on an objective that needs a human decision. Escalation is a
# successful outcome of the evaluation gate, not a failure of it.


def count_consecutive_reverts(
    module: str, log_dir: str = ".recurspec/evidence", branch: str | None = None
) -> int:
    """Reverts logged since the most recent KEEP (or the start of the log).

    Scoped to `branch` when given, so unrelated candidate branches for the
    same module don't inflate each other's stagnation count.
    """
    events = [
        e
        for e in read_events(module, log_dir)
        if e.get("event_type") in ("decision", "signal_d")
        and (branch is None or e.get("branch") == branch)
    ]
    count = 0
    for e in reversed(events):
        verdict = e.get("verdict")
        if verdict == "keep":
            break
        if verdict == "revert":
            count += 1
    return count


def count_total_reverts(
    module: str, log_dir: str = ".recurspec/evidence", branch: str | None = None
) -> int:
    """All revert decisions recorded for a branch across its full history.

    A legacy single-metric regression records its decision as ``signal_d``;
    other failure paths use ``decision``. Diagnostic Signal D events without a
    verdict are not attempts and therefore do not contribute to the ceiling.
    """
    return sum(
        1
        for event in read_events(module, log_dir)
        if event.get("event_type") in ("decision", "signal_d")
        and event.get("verdict") == "revert"
        and (branch is None or event.get("branch") == branch)
    )


def _entry_contradiction(entry: dict[str, Any], label: str) -> str | None:
    metric = entry.get("metric")
    if not isinstance(metric, str) or not metric.strip():
        return f"{label} is missing a metric name"
    if _numeric(entry.get("value")) is None:
        return f"{label} emitted no numeric or non-finite value"
    stage = entry.get("evidence_stage")
    if stage is not None and stage not in ("Measured", "Sampled", "Observed"):
        return (
            f"{label} claimed evidence_stage={stage!r}; a evaluation gate run can only "
            "produce Observed, Sampled, or Measured"
        )
    direction = entry.get("direction")
    if direction is not None:
        try:
            resolve_direction(metric, direction)
        except ValueError as exc:
            return f"{label}: {exc}"
    tier = entry.get("tier")
    if tier is not None:
        try:
            resolve_tier(tier)
        except ValueError as exc:
            return f"{label}: {exc}"
    return None


def telemetry_contradiction(payload: dict[str, Any]) -> str | None:
    """Detect a broken instrument (graybox red test).

    An instrument that reports success while omitting its own reading, or that
    claims an evidence stage it cannot support, is not trustworthy evidence.
    Handles both the legacy single-metric payload and a multi-metric payload
    carrying a top-level "metrics" list (checked entry by entry).
    """
    status = str(payload.get("status", "success")).lower()
    if status not in ("success", "ok", "pass", "passed"):
        return f"measure.sh reported status={status!r}"

    entries = payload.get("metrics")
    if isinstance(entries, list) and entries:
        for i, entry in enumerate(entries):
            if not isinstance(entry, dict):
                return f"metrics[{i}] is not an object"
            problem = _entry_contradiction(entry, f"metrics[{i}] ({entry.get('metric', '?')!r})")
            if problem:
                return problem
        return None

    return _entry_contradiction(payload, "measure.sh")
