# Contract Reconciler (L1)

> Reference archive: `docs/archive/2026-08-02-pre-redesign/architecture/architecture/RECONCILER/SYSTEM.md`
> Process detail: [contract-reconciliation.md](../../process/contract-reconciliation.md)

## 1. System Intent & Responsibility

Structural Feedback observer: detect **code drift**, **spec bloat**, and **test-seam** expansion; draft or split `SYSTEM.md` nodes; optionally emit Wayfinder tickets. Does not author product behavior; does not grade empirical metrics (Signal D is Evaluation Gate / Empirical Feedback — OW-13).

## 2. Sub-System Decomposition

**Atomic leaf (Phase 0).** Candidate later split: DriftScanner | BloatSplitter | SeamSync | TicketEmitter — only when interfaces stabilize.

## 3. Interface Contracts

| | |
|--|--|
| **Inputs** | Workspace tree, git status, line counts, AST/symbol index, existing architecture tree |
| **Outputs** | File→folder refactors, draft leaves, parent link updates, ADR stubs, ticket intents for Frontier Adapter |

## 4. Invariants (EARS + Epistemic Stage)

- **[Event-driven]** WHEN a spec file exceeds ~150 lines OR encodes more than three separable responsibilities THE SYSTEM SHALL convert it into a directory with root `SYSTEM.md` and child nodes.
  - `EvidenceStage:` Asserted (policy; automation OW-02)
- **[State-driven]** WHILE scanning source trees IF a file is unlinked in `docs/architecture` THE SYSTEM SHALL generate a draft leaf with Epistemic Stage `Unknown`.
  - `EvidenceStage:` Asserted
- **[Ubiquitous]** The Contract Reconciler SHALL NOT invent product requirements beyond structural drafts.
  - `EvidenceStage:` Asserted
- **[Conditional]** IF only metric regression is detected THEN THE SYSTEM SHALL defer to Evaluation Gate / Signal D (not structural auto-split alone).
  - `EvidenceStage:` Asserted · *Open:* OW-13

## 5. Architectural Decisions (ADRs)

- **ADR-001:** ~150 lines / >3 responsibilities as bloat triggers (heuristic, not a formal complexity metric).
- **ADR-002:** Drafts remain `Unknown` until Architect review (anti-authority drift; [research foundation](../../research/foundations.md) §3).

## 6. Leaf Execution & Test Seam

- **Implementation:** `src/contract-reconciler/auto_expander.py`
- **Tests:** `tests/test_contract-reconciler.py`
- **Open work:** OW-02

## 7. Measurement Seams

- **Primary metric:** `reconcile_false_split_rate` (target: low; measure via Architect rejections)
- **Evaluation Gate / checks:** `modules/contract-reconciler/measure.sh`, `checks.sh`
- **Branching:** never merge auto-splits without Outer Loop / human gate on consumer repos until dogfooded
