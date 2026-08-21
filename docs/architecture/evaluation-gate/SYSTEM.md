# Evaluation Gate (L1)

<!-- recurspec-contract: 1.0 -->

> Process: [evidence-cycle.md](../../process/evidence-cycle.md)
> Research: branching / autoresearch / verification ladder — [research/foundations.md](../../research/foundations.md) §4–§5

## 1. System Intent & Responsibility

Empirical Feedback infrastructure: explicit Best Known State (BKS) baselines, `measure.sh` / `checks.sh`, tiered metric evaluation, append-only evidence and Negative Pattern logs, bounded retry escalation, and candidate isolation via git worktrees. Feeds empirical reconciliation; enforces correctness backpressure before metric-based keep.

## 2. Sub-System Decomposition

**Atomic leaf (Phase 1).** Candidate later split: BaselineStore | WorktreeRunner | GrayboxProbeAdapter | KeepRevertPolicy.

## 3. Interface Contracts

- **Inputs:** Leaf §7 seams, worktree path, candidate description, completed Worker Pool
  authorization state, prior BKS metric vector, prior Negative Patterns.
- **Outputs:** Diff vs BKS, keep/revert/escalate decision, Signal D and Negative Pattern events in .recurspec/evidence/<module>/log.jsonl.

## 4. Invariants (EARS + Epistemic Stage)

- **[Ubiquitous]** The Evaluation Gate SHALL compare a candidate against the trunk BKS and SHALL promote a new baseline only through explicit `--record-baseline` after merge. (`test_evaluation_gate_promotes_baseline_only_when_explicitly_requested`)
  - `EvidenceStage:` Sampled
- **[Optional]** WHERE `--bks-metrics-only` is set THE SYSTEM SHALL give the Implementor
  the BKS metric vector and SHALL NOT include prior implementation source.
  (`test_implementor_bks_metrics_only_omits_source_even_when_files_are_named`)
  - `EvidenceStage:` Sampled
- **[Conditional]** IF the configured noise band is not below the regression
  tolerance THEN THE SYSTEM SHALL refuse the comparison rather than report every
  regression the tolerance exists to catch as neutral.
  (`test_compare_refuses_a_noise_band_that_swallows_the_tolerance`)
  - `EvidenceStage:` Sampled
- **[Ubiquitous]** Changed-module probe selection SHALL discover probes from the
  paths Contract Nodes declare in §7, not from a fixed directory name, so a project
  that keeps probes elsewhere cannot pass green having measured nothing.
  (`test_measurable_owners_discovers_probes_a_contract_declares_outside_modules`)
  - `EvidenceStage:` Sampled
- **[Event-driven]** WHEN `checks.sh` fails THE SYSTEM SHALL block keep regardless of primary metric improvement. (`test_runner_logs_negative_patterns_and_enforces_total_attempt_ceiling`)
  - `EvidenceStage:` Sampled
- **[Conditional]** IF telemetry self-contradiction is detected THEN THE SYSTEM SHALL flag the instrument broken and halt Empirical Feedback Contract Tree updates. (`test_telemetry_contradiction_multi_metric_missing_value`)
  - `EvidenceStage:` Sampled
- **[State-driven]** WHILE a Candidate branch is active THE SYSTEM SHALL isolate mutations from the baseline branch. (`test_isolated_candidate_keep_fast_forwards_baseline_and_disposes_worktree`; research: BranchBench / autoresearch branch–mutate–evaluate, [foundation](../../research/foundations.md) §4)
  - `EvidenceStage:` Sampled
- **[Conditional]** IF evaluation probes modify the Candidate worktree THEN THE SYSTEM
  SHALL refuse KEEP rather than merge a tree other than the one evaluated.
  (`test_isolated_candidate_refuses_probe_mutations_instead_of_merging_an_unevaluated_tree`)
  - `EvidenceStage:` Sampled
- **[Conditional]** IF merge authorization was not issued from completed Worker Pool
  maker/checker state THEN THE SYSTEM SHALL refuse evaluation; otherwise it SHALL append
  those identities to the evidence log. (`test_worker_pool_cannot_issue_merge_authorization_to_the_maker`,
  `test_completed_independent_check_persists_merge_authorization`)
  - `EvidenceStage:` Sampled
- **[Conditional]** IF the authorized Candidate branch or commit differs from the branch
  tip being evaluated THEN THE SYSTEM SHALL refuse evaluation before running probes.
  (`test_isolated_candidate_refuses_worker_authorization_for_another_candidate` and
  exact-tip lifecycle coverage)
  - `EvidenceStage:` Sampled
- **[Conditional]** IF a metric omits `tier` THEN THE SYSTEM SHALL treat it as `hard_gate`; `hard_gate`, `target`, and `optimization` regressions or unknown comparisons SHALL block keep, while `observation` SHALL never block. (`test_resolve_tier_defaults_to_hard_gate`, `test_evaluate_candidate_observation_never_blocks`)
  - `EvidenceStage:` Sampled
- **[Event-driven]** WHEN any candidate is reverted THE SYSTEM SHALL append one branch-scoped Negative Pattern and SHALL surface prior patterns before the next repair pass. (`test_evaluation_gate_logs_negative_patterns_and_enforces_total_attempt_ceiling`)
  - `EvidenceStage:` Sampled
- **[Conditional]** IF a branch reaches 5 consecutive reverts or 8 total reverts THEN THE SYSTEM SHALL return `ESCALATE` (exit code 3) instead of authorizing another automatic repair. (`test_evaluation_gate_logs_negative_patterns_and_enforces_total_attempt_ceiling`)
  - `EvidenceStage:` Sampled
- **[Optional]** WHERE a baseline `.recurspec/trusted-inputs.json` manifest is present
  THE SYSTEM SHALL pin every declared path into the Candidate worktree the same way as
  the fixed trusted set, and SHALL refuse evaluation rather than silently trust less
  than declared when the manifest is malformed or an entry escapes the repository.
  (`test_isolated_candidate_evaluates_against_a_manifest_declared_trusted_helper`,
  `test_load_trusted_manifest_fails_closed_on_malformed_content`,
  `test_load_trusted_manifest_refuses_a_path_that_escapes_the_repository`)
  - `EvidenceStage:` Sampled
- **[Conditional]** IF a decoded evidence event declares an unrecognized `event_type`,
  an unparseable `ts`, or a `module` that disagrees with the log it was read from THEN
  THE SYSTEM SHALL raise `EvidenceInstrumentError` rather than trust it.
  (`test_read_events_raises_on_a_module_that_disagrees_with_its_own_log`,
  `test_read_events_raises_on_an_unrecognized_event_type`,
  `test_read_events_raises_on_an_unparseable_timestamp`)
  - `EvidenceStage:` Sampled

## 5. Architectural Decisions (ADRs)

- **ADR-001:** Autoresearch-style edit → measure → keep/revert.
- **ADR-002:** Correctness backpressure mandatory; primary metric alone cannot authorize keep.
- **ADR-003:** Unknown behavioral boundaries become Research Frontiers (not silent merge).
- **ADR-004:** Multi-metric payloads use fail-closed tiers: untagged means `hard_gate`; only `observation` is non-blocking.
- **ADR-005:** KEEP authorization and BKS promotion are separate acts; the gate never silently promotes a candidate measurement.
- **ADR-006:** Retry is bounded and memory-bearing: every revert becomes a Negative Pattern; stagnation or the attempt ceiling escalates to a human. `ESCALATE` is the path when the Contract Node (the search space) may be wrong, not only when the candidate is wrong. Do not add a fourth gate outcome.

## 6. Leaf Execution & Test Seam

- **Current prototype:** `src/recurspec/metrics.py`, `src/recurspec/evaluation.py`, `src/recurspec/evidence.py`
- **Current implementation:** `src/recurspec/metrics.py` (comparison and tiers),
  `src/recurspec/evaluation.py`,
  `src/recurspec/modules_gate.py` (changed-module probes),
  `src/recurspec/evidence.py` (including opt-in corpus export).
- **Tests:** `tests/test_evaluation.py`, `tests/test_cli.py`, `tests/test_modules.py`
  (end-to-end coverage of every bundled `measure.sh` against `parse_measurement`),
  `tests/test_modules_gate.py` (changed-module probe selection),
  `tests/test_corpus.py` (corpus-export opt-in and redaction).
- **Lifecycle seam:** `evaluate_isolated_candidate` requires a clean checked-out baseline,
  a completed Worker Pool merge authorization, and an existing local Candidate branch. It
  evaluates the Candidate in a temporary worktree, refuses probe mutations, fast-forwards
  only on KEEP, persists authorization and evaluation evidence in the baseline worktree,
  and prunes the disposable worktree registration on every exit path.

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
- **Open questions:** none.
