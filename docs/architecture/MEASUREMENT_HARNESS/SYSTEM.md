# Measurement Harness (Level 1 Component)

## 1. System Intent & Responsibility
Manages per-component branching measurement: baseline capture, `measure.sh` / `checks.sh` harnesses, append-only metric logs, and hypothesis isolation via git worktrees. Feeds Back-Channel B (empirical reconciliation) in the dual back-channel loop.

## 2. Sub-System Decomposition
- **Atomic Leaf Component:** No further decomposition required for Phase 1.

## 3. Interface Contracts (Inputs & Outputs)
- **Inputs:** Leaf `SYSTEM.md` §7 Measurement Seams, isolated worktree path, hypothesis description.
- **Outputs:** Baseline/measurement diffs, keep/revert decision, `.measure/<component>/log.jsonl` entries.

## 4. Invariants (EARS Notation)
- [Ubiquitous] The Measurement Harness SHALL record a baseline metric before any optimization loop begins.
- [Event-driven] WHEN checks.sh fails THE SYSTEM SHALL block keep regardless of primary metric improvement.
- [Conditional] IF telemetry self-contradiction is detected THEN THE SYSTEM SHALL flag the instrument as broken and halt Back-Channel B updates.
- [State-driven] WHILE a hypothesis branch is active THE SYSTEM SHALL isolate mutations from the main blueprint branch.

## 5. Architectural Decisions (ADRs)
- **ADR-001:** Adopted autoresearch-style edit → measure → keep/revert loop for component optimization.
- **ADR-002:** Correctness backpressure (checks.sh) is mandatory; primary metric alone cannot authorize keep.

## 6. Leaf Execution & Test Seam
- **Implementation File:** `src/measurement_harness/runner.py`
- **Test Surface Seam:** `tests/test_measurement_harness.py`

## 7. Measurement Seams
- **Primary Metric:** `harness_run_latency_ms` — target ≤ 5000ms for full component measure cycle
- **Harness:** `components/MEASUREMENT_HARNESS/measure.sh`
- **Correctness Backpressure:** `components/MEASUREMENT_HARNESS/checks.sh`
- **Branching Policy:** One worktree per hypothesis; merge only on Outer Loop Auditor approval
