# Structure Gate (L1)

<!-- recurspec-contract: 1.0 -->

> Reference archive: `docs/archive/2026-08-02-pre-redesign/architecture/architecture/AST_GATEKEEPER/SYSTEM.md`
> Research: SDB / dual-state verification — [research/foundations.md](../../research/foundations.md) §2–§3, §5 (L2 rule/schema)

## 1. System Intent & Responsibility

Deterministic **L2** gate: Python AST analysis enforces zero-drift and seam coverage
between code and the Contract Tree. Rejects commits that would land stochastic agent
output without structural verification.

## 2. Sub-System Decomposition

**Atomic leaf (Phase 0).** Later: SpecCoverageCheck | ExportTestSeamCheck | PolicyPack — when each has independent config seams.

## 3. Interface Contracts

- **Inputs:** repository root, source root, Contract Tree root, optional changed-file list.
- **Outputs:** immutable result with sorted diagnostics; JSON/text CLI output and non-zero
  exit on drift or instrument failure.

## 4. Invariants (EARS + Epistemic Stage)

- **[Ubiquitous]** The Gatekeeper SHALL verify that exported symbols intended as seams
  belong to a Contract Node and that declared implementation/test paths exist.
  (`test_structure_gate_accepts_contract_owned_python_with_a_real_test_surface`)
  - `EvidenceStage:` Sampled
- **[Conditional]** IF a module declares literal `__all__` exports THEN THE SYSTEM SHALL
  use that set as its public surface; every owned exported surface SHALL have a declared
  test seam. (`test_structure_gate_uses_explicit_exports_and_requires_their_test_surface`)
  - `EvidenceStage:` Sampled
- **[Conditional]** IF un-specced code drift is detected under active policy THEN THE SYSTEM SHALL exit non-zero.
  - `EvidenceStage:` Sampled
- **[Ubiquitous]** The Gatekeeper SHALL NOT use L4 model-judge scores as a substitute for L1/L2 results. ([research foundation](../../research/foundations.md) §5)
  - `EvidenceStage:` Unknown

## 5. Architectural Decisions (ADRs)

- **ADR-001:** Derive implementation ownership and test surfaces from Contract Node §6;
  do not maintain a parallel structure-policy file.
- **ADR-003:** Use Python's concrete AST for Python symbols and a narrow Markdown §6
  extractor for declared paths. Unsupported source languages are refused, not guessed.
- **ADR-002:** Gatekeeper is Auditor-side infrastructure; Implementor may run it locally but cannot waive failures without Outer Loop.

## 6. Leaf Execution & Test Seam

- **Implementation:** `src/recurspec/structure_gate.py`; public seam `check_structure()`.
- **Tests:** `tests/test_structure_gate.py` plus CLI coverage in `tests/test_cli.py`.
- **Roadmap:** R-300.

## 7. Measurement Seams

- **Primary metric:** `gate_false_negative_rate` on seeded drift fixtures (target → 0 on fixture set)
- **Evaluation Gate / checks:** `modules/structure-gate/measure.sh`, `checks.sh`

## 8. Technology Resolution

- **Decision class:** BUILD
- **Justification:** Python's standard-library `ast` already supplies the required parser;
  the small missing piece is Recurspec-specific policy joining source paths to Contract
  Node §6 declarations. An external graph runtime would enlarge installation and adapter
  surface without improving this leaf's required checks.
- **Selected:** Python `ast` plus `pathlib`, wrapped by `check_structure()`.
- **Standard / protocol:** Python AST; Contract Node 1.0 Markdown §6 declarations.
- **Alternatives considered:**

  | Option | Why not |
  |---|---|
  | Interactive `graphgraph` / `code-review-graph` tooling | Not an installable runtime dependency or stable package protocol; would make the CLI environment-dependent. |
  | A generic dependency-cruiser-style tool | Enforces import boundaries, not "does this symbol have a parent Contract Node," which needs the tree as ground truth. |

- **Fit gap:** `ast` has no notion of a Contract Tree or required test seam; the adapter
  owns only §6 path extraction, ownership joins, and deterministic diagnostics.
- **Seam:** `src/recurspec/structure_gate.py`.
- **Exit cost:** LOW — symbol extraction is isolated behind `check_structure()` and can
  accept another language parser later without changing policy diagnostics.
- **Cost model:** no service spend; local compute only.
- **Liability transferred:** Python parsing correctness.
- **Operational owner:** us.
- **Failure mode:** a false negative lets un-specced drift land; measured directly by the
  primary metric above.
- **Open questions:** none outside ROADMAP R-300.
