# AST Gatekeeper (L1)

> Reference archive: `docs/archive/2026-08-02-pre-redesign/architecture/architecture/AST_GATEKEEPER/SYSTEM.md`  
> Research: SDB / dual-state verification — [research/foundation.md](../../research/foundation.md) §2–§3, §5 (L2 rule/schema)

## 1. System Intent & Responsibility

Deterministic **L2** gate: AST / graph analysis (`graphgraph`, `code-review-graph`, or equivalent) enforces zero-drift and seam coverage between code and the architecture tree. Rejects commits that would land stochastic agent output without structural verification.

## 2. Sub-System Decomposition

**Atomic leaf (Phase 0).** Later: SpecCoverageCheck | ExportTestSeamCheck | PolicyPack — when each has independent config seams.

## 3. Interface Contracts

| | |
|--|--|
| **Inputs** | Source AST/index, architecture node set, optional pre-commit file list |
| **Outputs** | PASS/FAIL, drift diagnostics, non-zero exit on fail |

## 4. Invariants (EARS + Epistemic Stage)

- **[Ubiquitous]** The Gatekeeper SHALL verify that exported symbols intended as seams have a corresponding test surface when policy requires it.  
  - `EvidenceStage:` Sampled · OW-04
- **[Conditional]** IF un-specced code drift is detected under active policy THEN THE SYSTEM SHALL exit non-zero.  
  - `EvidenceStage:` Sampled
- **[Ubiquitous]** The Gatekeeper SHALL NOT use L4 model-judge scores as a substitute for L1/L2 results.  
  - `EvidenceStage:` Inferred ([research foundation](../../research/foundation.md) §5)

## 5. Architectural Decisions (ADRs)

- **ADR-001:** Prefer project graph tools (graphgraph / code-review-graph) over ad-hoc regex for symbol seams.
- **ADR-002:** Gatekeeper is Auditor-side infrastructure; Implementor may run it locally but cannot waive failures without Outer Loop.

## 6. Leaf Execution & Test Seam

- **Implementation:** `src/ast_gatekeeper/checker.py`
- **Tests:** `tests/test_ast_gatekeeper.py`
- **Open work:** OW-04 (blocked by OW-02)

## 7. Measurement Seams

- **Primary metric:** `gate_false_negative_rate` on seeded drift fixtures (target → 0 on fixture set)
- **Harness / checks:** `components/ast-gatekeeper/measure.sh`, `checks.sh`
