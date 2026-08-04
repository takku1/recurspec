# Spec Engine (L1)

> Reference archive: `docs/archive/2026-08-02-pre-redesign/architecture/architecture/SPEC_ENGINE/SYSTEM.md`

## 1. System Intent & Responsibility

Create, validate, and format fractal `SYSTEM.md` contracts using **EARS** patterns and Epistemic Stage tags. Owns structural validity of the spec tree, not runtime code of consumer products.

## 2. Sub-System Decomposition

**Atomic leaf (Phase 0).** Further split only if generator vs validator vs template-linter gain independent seams.

## 3. Interface Contracts

| | |
|--|--|
| **Inputs** | Component title, intent prose, candidate invariants, optional parent path, child index |
| **Outputs** | Validated Markdown `SYSTEM.md`; validation diagnostics (missing EARS keywords, missing §6/§7 on leaves) |

## 4. Invariants (EARS + Epistemic Stage)

- **[Ubiquitous]** The Spec Engine SHALL format invariants using EARS keywords: Ubiquitous, Event-driven, State-driven, Conditional.  
  - `EvidenceStage:` Observed (process); automation Sampled pending OW-01  
  - *Research:* Mavin et al., RE'09 — see [research/foundation.md](../../research/foundation.md) §1
- **[Conditional]** IF a node is an Atomic Leaf THEN THE SYSTEM SHALL require Section 6 (Test Seam) and Section 7 (Measurement Seams).  
  - `EvidenceStage:` Observed
- **[Conditional]** IF an invariant lacks an Epistemic Stage tag THEN THE SYSTEM SHALL treat it as `Unknown` and flag for Architect review.  
  - `EvidenceStage:` Inferred

## 5. Architectural Decisions (ADRs)

- **ADR-001:** Strict EARS keywords only (no free-form “shall” without pattern class).
- **ADR-002:** Epistemic Stages are mandatory metadata; Sampled ≠ Proved ([research foundation](../../research/foundation.md) §5).

## 6. Leaf Execution & Test Seam

- **Implementation:** `src/spec_engine/generator.py`
- **Tests / checks:** `tests/test_spec_engine.py` · component `checks.sh` when scaffolded
- **Open work:** OW-01

## 7. Measurement Seams

- **Primary metric:** `ears_validation_pass_rate` (target: 1.0 on generated nodes)
- **Secondary:** `specs_generated_per_sec` (informational)
- **Harness:** `components/spec-engine/measure.sh` (scaffold with OW-05)
- **Backpressure:** `components/spec-engine/checks.sh` must pass before keep
- **Branching:** isolated worktree; Outer Loop keep/revert only
