# Measurement Harness (L1)

> Reference archive: `docs/archive/2026-08-02-pre-redesign/architecture/architecture/MEASUREMENT_HARNESS/SYSTEM.md`  
> Process: [dual-backchannel-loop.md](../../process/dual-backchannel-loop.md)  
> Research: branching / autoresearch / verification ladder — [research/foundation.md](../../research/foundation.md) §4–§5

## 1. System Intent & Responsibility

Back-Channel B infrastructure: baselines, `measure.sh` / `checks.sh`, append-only metric logs, hypothesis isolation via git worktrees. Feeds empirical reconciliation; enforces correctness backpressure before metric-based keep.

## 2. Sub-System Decomposition

**Atomic leaf (Phase 1).** Candidate later split: BaselineStore | WorktreeRunner | GrayboxProbeAdapter | KeepRevertPolicy.

## 3. Interface Contracts

| | |
|--|--|
| **Inputs** | Leaf §7 seams, worktree path, hypothesis description, prior baseline |
| **Outputs** | Diff vs baseline, keep/revert decision record, `.measure/<component>/log.jsonl` entries |

## 4. Invariants (EARS + Epistemic Stage)

- **[Ubiquitous]** The Harness SHALL record a baseline metric before an optimization loop begins.  
  - `EvidenceStage:` Observed (design); automation OW-05 / OW-11
- **[Event-driven]** WHEN `checks.sh` fails THE SYSTEM SHALL block keep regardless of primary metric improvement.  
  - `EvidenceStage:` Observed (policy)
- **[Conditional]** IF telemetry self-contradiction is detected THEN THE SYSTEM SHALL flag the instrument broken and halt Back-Channel B blueprint updates.  
  - `EvidenceStage:` Inferred (graybox practice)
- **[State-driven]** WHILE a hypothesis branch is active THE SYSTEM SHALL isolate mutations from the main blueprint branch.  
  - `EvidenceStage:` Sampled · *Research:* BranchBench / autoresearch branch–mutate–evaluate ([foundation](../../research/foundation.md) §4)

## 5. Architectural Decisions (ADRs)

- **ADR-001:** Autoresearch-style edit → measure → keep/revert.
- **ADR-002:** Correctness backpressure mandatory; primary metric alone cannot authorize keep.
- **ADR-003:** Unknown behavioral boundaries emit Type B Wayfinder tickets (not silent merge).

## 6. Leaf Execution & Test Seam

- **Implementation:** `src/measurement_harness/runner.py` (plus existing `harness/*.py` prototypes)
- **Tests:** `tests/test_measurement_harness.py`
- **Open work:** OW-05 (blocked by OW-04), OW-11, OW-12

## 7. Measurement Seams (meta)

- **Primary metric:** `harness_run_latency_ms` (target ≤ 5000ms for full component cycle)
- **Harness:** `components/measurement-harness/measure.sh`
- **Backpressure:** `components/measurement-harness/checks.sh`
- **Log format:** append-only JSONL under `.measure/<component>/`
