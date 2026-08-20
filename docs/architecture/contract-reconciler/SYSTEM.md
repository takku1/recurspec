# Contract Reconciler (L1)

<!-- recurspec-contract: 1.0 -->

> Process detail: [contract-reconciliation.md](../../process/contract-reconciliation.md)

## 1. System Intent & Responsibility

Structural Feedback observer: detect **code drift**, **spec bloat**, and **test-seam**
expansion; emit deterministic, reviewable draft actions. Does not mutate contracts, author
product behavior, or grade empirical metrics (Signal D is Evaluation Gate / Empirical
Feedback).

## 2. Sub-System Decomposition

**Atomic leaf (Phase 0).** Candidate later split: DriftScanner | BloatSplitter | SeamSync | TicketEmitter — only when interfaces stabilize.

## 3. Interface Contracts

- **Inputs:** Workspace tree, optional changed-file set, Structure Gate diagnostics,
  Contract Tree line counts, optional evidence events.
- **Outputs:** Immutable draft-leaf, split-review, contract-repair, and test-seam-review
  actions; count of deferred Signal D events; stable JSON/text CLI output.

## 4. Invariants (EARS + Epistemic Stage)

- **[Event-driven]** WHEN a Contract Node exceeds 150 lines THE SYSTEM SHALL emit a
  split-review action and SHALL NOT choose child responsibilities without Architect
  review. (`test_reconciler_proposes_review_for_bloat_and_uncontracted_test_seams`)
  - `EvidenceStage:` Sampled
- **[Conditional]** IF a Contract Node explicitly declares more than three semicolon-
  separated `Responsibilities` THEN THE SYSTEM SHALL emit a split-review action.
  (`test_reconciler_proposes_split_for_four_explicit_separable_responsibilities`)
  - `EvidenceStage:` Sampled
- **[State-driven]** WHILE scanning source trees IF a file is unlinked in `docs/architecture` THE SYSTEM SHALL generate a draft leaf with Epistemic Stage `Unknown`.
  (`test_reconciler_turns_uncontracted_source_into_an_unknown_draft_without_writing`)
  - `EvidenceStage:` Sampled
- **[Ubiquitous]** The Contract Reconciler SHALL NOT invent product requirements beyond structural drafts.
  (`test_reconciler_turns_uncontracted_source_into_an_unknown_draft_without_writing`)
  - `EvidenceStage:` Sampled
- **[Conditional]** IF a test file is absent from Contract Node §6 declarations THEN THE
  SYSTEM SHALL emit a test-seam-review action. (`test_reconciler_proposes_review_for_bloat_and_uncontracted_test_seams`)
  - `EvidenceStage:` Sampled
- **[Conditional]** IF only metric regression is detected THEN THE SYSTEM SHALL defer to Evaluation Gate / Signal D (not structural auto-split alone). (`test_reconciler_defers_metric_only_feedback_to_the_evaluation_gate`)
  - `EvidenceStage:` Sampled

## 5. Architectural Decisions (ADRs)

- **ADR-001:** ~150 lines / >3 responsibilities as bloat triggers (heuristic, not a formal complexity metric).
- **ADR-002:** Drafts remain `Unknown` until Architect review (anti-authority drift; [research foundation](../../research/foundations.md) §3).

## 6. Leaf Execution & Test Seam

- **Implementation:** `src/recurspec/reconcile.py`; public seam `plan_reconciliation()`.
- **Tests:** `tests/test_reconcile.py`, plus CLI coverage in `tests/test_cli.py`.

## 7. Measurement Seams

- **Primary metric:** `seeded_reconciliation_precision` (target: 1.0 on the fixture set).
- **Operational metric:** `reconcile_false_split_rate` requires Architect accept/reject
  evidence and remains `Unknown` until those judgments exist; it is never defaulted.
- **Evaluation Gate / checks:** `modules/contract-reconciler/measure.sh`, `checks.sh`
- **Branching:** never merge auto-splits without Outer Loop / human gate on consumer repos until dogfooded

## 8. Technology Resolution

- **Decision class:** BUILD
- **Justification:** Differentiator. Turning Structural Feedback (drift between code and
  the Contract Tree) into draft contract edits is Recurspec's own reconciliation policy;
  no vendor tool understands this repository's `SYSTEM.md` shape.
- **Selected:** Python module under `src/recurspec/`, consuming the deterministic
  `StructureResult` policy seam from `structure_gate.py`.
- **Standard / protocol:** internal immutable dataclasses and stable JSON output.
- **Alternatives considered:**

  | Option | Why not |
  |---|---|
  | Generic dead-code / drift linters (e.g. Vulture, ts-prune equivalents) | Detect unused symbols, not "code without a parent Contract Node," which is a Recurspec-specific relationship. |
  | A general dependency-graph database | Answers "what imports what," not "does this match the declared architecture," which needs the Contract Tree as ground truth. |

- **Fit gap:** the Structure Gate reports drift but does not decide whether it calls for a
  draft leaf, repair review, split review, or test-seam review; this module owns that
  proposal policy.
- **Seam:** `src/recurspec/reconcile.py`.
- **Exit cost:** LOW — reconciliation drafts are proposals, never auto-committed.
- **Cost model:** no service spend; local compute only.
- **Liability transferred:** none.
- **Operational owner:** us.
- **Failure mode:** a false-positive split proposes an unwanted refactor; mitigated by
  requiring human review before merge (see §7 Branching).
- **Open questions:** none.
