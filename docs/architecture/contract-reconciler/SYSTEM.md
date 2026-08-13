# Contract Reconciler (L1)

<!-- recurspec-contract: 1.0 -->

> Reference archive: `docs/archive/2026-08-02-pre-redesign/architecture/architecture/RECONCILER/SYSTEM.md`
> Process detail: [contract-reconciliation.md](../../process/contract-reconciliation.md)

## 1. System Intent & Responsibility

Structural Feedback observer: detect **code drift**, **spec bloat**, and **test-seam** expansion; draft or split `SYSTEM.md` nodes; optionally emit Wayfinder tickets. Does not author product behavior; does not grade empirical metrics (Signal D is Evaluation Gate / Empirical Feedback — OW-13).

## 2. Sub-System Decomposition

**Atomic leaf (Phase 0).** Candidate later split: DriftScanner | BloatSplitter | SeamSync | TicketEmitter — only when interfaces stabilize.

## 3. Interface Contracts

- **Inputs:** Workspace tree, git status, line counts, AST/symbol index, existing architecture tree.
- **Outputs:** File→folder refactors, draft leaves, parent link updates, ADR stubs, ticket intents for Frontier Adapter.

## 4. Invariants (EARS + Epistemic Stage)

- **[Event-driven]** WHEN a spec file exceeds ~150 lines OR encodes more than three separable responsibilities THE SYSTEM SHALL convert it into a directory with root `SYSTEM.md` and child nodes. (policy; automation OW-02)
  - `EvidenceStage:` Unknown
- **[State-driven]** WHILE scanning source trees IF a file is unlinked in `docs/architecture` THE SYSTEM SHALL generate a draft leaf with Epistemic Stage `Unknown`.
  - `EvidenceStage:` Unknown
- **[Ubiquitous]** The Contract Reconciler SHALL NOT invent product requirements beyond structural drafts.
  - `EvidenceStage:` Unknown
- **[Conditional]** IF only metric regression is detected THEN THE SYSTEM SHALL defer to Evaluation Gate / Signal D (not structural auto-split alone). (open: OW-13)
  - `EvidenceStage:` Unknown

## 5. Architectural Decisions (ADRs)

- **ADR-001:** ~150 lines / >3 responsibilities as bloat triggers (heuristic, not a formal complexity metric).
- **ADR-002:** Drafts remain `Unknown` until Architect review (anti-authority drift; [research foundation](../../research/foundations.md) §3).

## 6. Leaf Execution & Test Seam

- **Implementation:** not yet built; planned seam `src/recurspec/reconcile.py`.
- **Tests:** none yet; planned `tests/test_reconcile.py`.
- **Open work:** OW-02; tracked as ROADMAP R-301 (blocked by R-300).

## 7. Measurement Seams

- **Primary metric:** `reconcile_false_split_rate` (target: low; measure via Architect rejections)
- **Evaluation Gate / checks:** `modules/contract-reconciler/measure.sh`, `checks.sh`
- **Branching:** never merge auto-splits without Outer Loop / human gate on consumer repos until dogfooded

## 8. Technology Resolution

- **Decision class:** BUILD
- **Justification:** Differentiator. Turning Structural Feedback (drift between code and
  the Contract Tree) into draft contract edits is Recurspec's own reconciliation policy;
  no vendor tool understands this repository's `SYSTEM.md` shape.
- **Selected:** Python module under `src/recurspec/`, reusing the existing
  `graphgraph` / `code-review-graph`-style structural signals already used ad hoc during
  development, wrapped by a narrow adapter rather than depended on directly.
- **Standard / protocol:** none — internal.
- **Alternatives considered:**

  | Option | Why not |
  |---|---|
  | Generic dead-code / drift linters (e.g. Vulture, ts-prune equivalents) | Detect unused symbols, not "code without a parent Contract Node," which is a Recurspec-specific relationship. |
  | A general dependency-graph database | Answers "what imports what," not "does this match the declared architecture," which needs the Contract Tree as ground truth. |

- **Fit gap:** existing structural-analysis tools have no notion of a Contract Tree; the
  reconciliation policy (draft vs. split vs. ticket) stays custom.
- **Seam:** `src/recurspec/reconcile.py` (planned).
- **Exit cost:** LOW — reconciliation drafts are proposals, never auto-committed.
- **Cost model:** no service spend; local compute only.
- **Liability transferred:** none.
- **Operational owner:** us.
- **Failure mode:** a false-positive split proposes an unwanted refactor; mitigated by
  requiring human review before merge (see §7 Branching).
- **Open questions:** OW-02; ROADMAP R-300 (uncontracted-symbol detection) must land first.
