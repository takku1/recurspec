# Evaluation Gate (L1)

<!-- recurspec-contract: 1.0 -->

> Reference archive: `docs/archive/2026-08-02-pre-redesign/architecture/architecture/MEASUREMENT_HARNESS/SYSTEM.md`
> Process: [evidence-cycle.md](../../process/evidence-cycle.md)
> Research: branching / autoresearch / verification ladder — [research/foundations.md](../../research/foundations.md) §4–§5

## 1. System Intent & Responsibility

Empirical Feedback infrastructure: explicit Best Known State (BKS) baselines, `measure.sh` / `checks.sh`, tiered metric evaluation, append-only evidence and Negative Pattern logs, bounded retry escalation, and candidate isolation via git worktrees. Feeds empirical reconciliation; enforces correctness backpressure before metric-based keep.

## 2. Sub-System Decomposition

**Atomic leaf (Phase 1).** Candidate later split: BaselineStore | WorktreeRunner | GrayboxProbeAdapter | KeepRevertPolicy.

## 3. Interface Contracts

- **Inputs:** Leaf §7 seams, worktree path, candidate description, prior BKS metric vector, prior Negative Patterns.
- **Outputs:** Diff vs BKS, keep/revert/escalate decision, Signal D and Negative Pattern events in .recurspec/evidence/<module>/log.jsonl.

## 4. Invariants (EARS + Epistemic Stage)

- **[Ubiquitous]** The Evaluation Gate SHALL compare a candidate against the trunk BKS and SHALL promote a new baseline only through explicit `--record-baseline` after merge. (`find_baseline` and baseline-promotion unit coverage; production automation OW-05)
  - `EvidenceStage:` Sampled
- **[Event-driven]** WHEN `checks.sh` fails THE SYSTEM SHALL block keep regardless of primary metric improvement. (`test_runner_logs_negative_patterns_and_enforces_total_attempt_ceiling`)
  - `EvidenceStage:` Sampled
- **[Conditional]** IF telemetry self-contradiction is detected THEN THE SYSTEM SHALL flag the instrument broken and halt Empirical Feedback blueprint updates. (legacy and multi-metric contradiction tests)
  - `EvidenceStage:` Sampled
- **[State-driven]** WHILE a candidate branch is active THE SYSTEM SHALL isolate mutations from the main blueprint branch. (policy specified; production worktree lifecycle remains OW-05; research: BranchBench / autoresearch branch–mutate–evaluate, [foundation](../../research/foundations.md) §4)
  - `EvidenceStage:` Unknown
- **[Conditional]** IF a metric omits `tier` THEN THE SYSTEM SHALL treat it as `hard_gate`; `hard_gate`, `target`, and `optimization` regressions or unknown comparisons SHALL block keep, while `observation` SHALL never block. (`resolve_tier` / `evaluate_candidate` unit coverage)
  - `EvidenceStage:` Sampled
- **[Event-driven]** WHEN any candidate is reverted THE SYSTEM SHALL append one branch-scoped Negative Pattern and SHALL surface prior patterns before the next repair pass. (runner integration coverage)
  - `EvidenceStage:` Sampled
- **[Conditional]** IF a branch reaches 5 consecutive reverts or 8 total reverts THEN THE SYSTEM SHALL return `ESCALATE` (exit code 3) instead of authorizing another automatic repair. (streak, branch-scope, total-ceiling, and runner integration coverage)
  - `EvidenceStage:` Sampled

## 5. Architectural Decisions (ADRs)

- **ADR-001:** Autoresearch-style edit → measure → keep/revert.
- **ADR-002:** Correctness backpressure mandatory; primary metric alone cannot authorize keep.
- **ADR-003:** Unknown behavioral boundaries emit Type B Wayfinder tickets (not silent merge).
- **ADR-004:** Multi-metric payloads use fail-closed tiers: untagged means `hard_gate`; only `observation` is non-blocking.
- **ADR-005:** KEEP authorization and BKS promotion are separate acts; the gate never silently promotes a candidate measurement.
- **ADR-006:** Retry is bounded and memory-bearing: every revert becomes a Negative Pattern; stagnation or the attempt ceiling escalates to a human.

## 6. Leaf Execution & Test Seam

- **Current prototype:** `src/recurspec/metrics.py`, `src/recurspec/evaluation.py`, `src/recurspec/evidence.py`
- **Current implementation:** `src/recurspec/evaluation.py`
- **Tests:** `python -m pytest tests/test_evaluation.py -q` (59 sampled checks)
- **Open work:** OW-05 (worktree lifecycle; blocked by OW-04), OW-10 (packet/report templates and dogfood), OW-12, OW-13 (Signal D consumer)

## 7. Measurement Seams (meta)

- **Primary metric:** `evaluation gate_run_latency_ms` (target ≤ 5000ms for full module cycle)
- **Evaluation Gate:** `modules/evaluation-gate/measure.sh`
- **Backpressure:** `modules/evaluation-gate/checks.sh`
- **Log format:** append-only JSONL under `.recurspec/evidence/<module>/`
- **Accepted payloads:** legacy single `{"metric": ..., "value": ...}` or `{"metrics": [{"metric": ..., "value": ..., "tier": ...}]}`
- **Decision seam:** `KEEP=0` · `REVERT=1` · evaluation gate error `=2` · `ESCALATE=3`
- **BKS rule:** only trunk `baseline` / accepted `measurement` events are eligible; candidate events never auto-promote

## 8. Technology Resolution

- **Decision class:** BUILD
- **Justification:** Differentiator. Tiered keep/revert/escalate decisioning over an
  append-only evidence log and bounded Negative Pattern memory is Recurspec's own method;
  no vendor sells this specific policy.
- **Selected:** Python standard library only (`subprocess`, `shutil`, `os`, `json`) driving
  consumer-owned `measure.sh` / `checks.sh` scripts and `git worktree` for isolation.
- **Standard / protocol:** none — internal; the worktree isolation seam is `git worktree`.
- **Alternatives considered:**

  | Option | Why not |
  |---|---|
  | A CI-native gate (GitHub Actions reusable workflow) | Couples the decision policy to one CI vendor; Recurspec must also run locally before any commit exists. |
  | An experimentation platform (e.g. GrowthBook, Statsig) | Built for live traffic experiments, not build-time correctness-gated code candidates. |
  | Hand-rolled shell only, no Python | Loses structured tiered-metric parsing and the typed KEEP/REVERT/ESCALATE contract tests exercise today. |

- **Fit gap:** none of the alternatives model correctness-gated, bounded-retry candidate
  evaluation; the decision logic stays custom by intent.
- **Seam:** `src/recurspec/evaluation.py`, `src/recurspec/metrics.py`, `src/recurspec/evidence.py`.
- **Exit cost:** LOW — the module boundary is the evaluation seam; `measure.sh` / `checks.sh`
  contracts are consumer-owned and do not change if the Python driver is replaced.
- **Cost model:** no service spend; local compute only.
- **Liability transferred:** none.
- **Operational owner:** us.
- **Failure mode:** a broken instrument (non-numeric reading, contradictory telemetry)
  reverts the candidate rather than guessing; see invariant 3.
- **Open questions:** OW-05 (worktree lifecycle automation).
