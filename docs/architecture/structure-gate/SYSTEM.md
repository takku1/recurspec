# Structure Gate (L1)

<!-- recurspec-contract: 1.0 -->

> Reference archive: `docs/archive/2026-08-02-pre-redesign/architecture/architecture/AST_GATEKEEPER/SYSTEM.md`
> Research: SDB / dual-state verification — [research/foundations.md](../../research/foundations.md) §2–§3, §5 (L2 rule/schema)

## 1. System Intent & Responsibility

Deterministic **L2** gate: AST / graph analysis (`graphgraph`, `code-review-graph`, or equivalent) enforces zero-drift and seam coverage between code and the architecture tree. Rejects commits that would land stochastic agent output without structural verification.

## 2. Sub-System Decomposition

**Atomic leaf (Phase 0).** Later: SpecCoverageCheck | ExportTestSeamCheck | PolicyPack — when each has independent config seams.

## 3. Interface Contracts

- **Inputs:** Source AST/index, architecture node set, optional pre-commit file list.
- **Outputs:** PASS/FAIL, drift diagnostics, non-zero exit on fail.

## 4. Invariants (EARS + Epistemic Stage)

- **[Ubiquitous]** The Gatekeeper SHALL verify that exported symbols intended as seams have a corresponding test surface when policy requires it. (OW-04)
  - `EvidenceStage:` Unknown
- **[Conditional]** IF un-specced code drift is detected under active policy THEN THE SYSTEM SHALL exit non-zero.
  - `EvidenceStage:` Unknown
- **[Ubiquitous]** The Gatekeeper SHALL NOT use L4 model-judge scores as a substitute for L1/L2 results. ([research foundation](../../research/foundations.md) §5)
  - `EvidenceStage:` Unknown

## 5. Architectural Decisions (ADRs)

- **ADR-001:** Prefer project graph tools (graphgraph / code-review-graph) over ad-hoc regex for symbol seams.
- **ADR-002:** Gatekeeper is Auditor-side infrastructure; Implementor may run it locally but cannot waive failures without Outer Loop.

## 6. Leaf Execution & Test Seam

- **Implementation:** not yet built; planned seam `src/recurspec/structure_gate.py`.
- **Tests:** none yet; planned `tests/test_structure_gate.py`.
- **Open work:** OW-04 (blocked by OW-02); tracked as ROADMAP R-300.

## 7. Measurement Seams

- **Primary metric:** `gate_false_negative_rate` on seeded drift fixtures (target → 0 on fixture set)
- **Evaluation Gate / checks:** `modules/structure-gate/measure.sh`, `checks.sh`

## 8. Technology Resolution

- **Decision class:** WRAP
- **Justification:** The AST/graph traversal itself is a commodity capability; only the
  policy ("every exported seam needs a test, every source file needs a parent Contract
  Node") is Recurspec-specific.
- **Selected:** the project's own `graphgraph` / `code-review-graph` MCP tooling (already
  used interactively during development) wrapped by a narrow policy-check adapter.
- **Standard / protocol:** none — internal; consumes whatever graph/AST index the wrapped
  tool exposes.
- **Alternatives considered:**

  | Option | Why not |
  |---|---|
  | Hand-rolled `ast` module traversal | Reimplements graph/import resolution the wrapped tools already provide. |
  | A generic dependency-cruiser-style tool | Enforces import boundaries, not "does this symbol have a parent Contract Node," which needs the tree as ground truth. |

- **Fit gap:** graph/AST tools have no notion of a Contract Tree or a required test seam;
  the wrapper owns that policy check.
- **Seam:** `src/recurspec/structure_gate.py` (planned).
- **Exit cost:** LOW — the wrapped tool is swappable behind the same policy-check adapter.
- **Cost model:** no service spend; local compute only.
- **Liability transferred:** graph/AST parsing correctness.
- **Operational owner:** us.
- **Failure mode:** a false negative lets un-specced drift land; measured directly by the
  primary metric above.
- **Open questions:** OW-04; ROADMAP R-300 must land before this leaf can be implemented.
