# Recursive System Specification Engine (L0 Root)

## 1. System Intent & Responsibility

RSS is a **self-healing, multi-signal specification engine** for AI-assisted software engineering. It maintains a fractal tree of machine-usable contracts (`SYSTEM.md`), executes work through Wayfinder frontiers, and closes the loop with dual back-channels (structural + empirical) under an SDB verification gate.

**Does not own:** product application code of consumer repos; those *use* RSS process and may mirror this tree shape.

## 2. Sub-System Decomposition

| Component | Path | Responsibility |
|-----------|------|----------------|
| Spec Engine | [spec-engine/SYSTEM.md](./spec-engine/SYSTEM.md) | Create/validate EARS `SYSTEM.md` trees |
| Reconciler | [reconciler/SYSTEM.md](./reconciler/SYSTEM.md) | Structural sensory signals; auto-expand |
| Wayfinder Connector | [wayfinder-connector/SYSTEM.md](./wayfinder-connector/SYSTEM.md) | Leaf → frontier tickets |
| AST Gatekeeper | [ast-gatekeeper/SYSTEM.md](./ast-gatekeeper/SYSTEM.md) | Deterministic zero-drift / coverage checks |
| Measurement Harness | [measurement-harness/SYSTEM.md](./measurement-harness/SYSTEM.md) | Branching measure; Back-Channel B inputs |

Process (not code modules): [dual-backchannel-loop](../process/dual-backchannel-loop.md), [multi-signal-reconciler](../process/multi-signal-reconciler.md).  
Incomplete work: [open-work.md](../open-work.md).  
Research: [research/foundation.md](../research/foundation.md).

## 3. Interface Contracts

| Direction | Artifacts |
|-----------|-----------|
| **Inputs** | Product vision / NL scope; git diffs; existing code ASTs; measure baselines |
| **Outputs** | Fractal `docs/architecture/**/SYSTEM.md`; Wayfinder tickets; pass/fail gate reports; baseline logs under `.measure/` |

## 4. Invariants (EARS + Epistemic Stage)

- **[Ubiquitous]** The Root System SHALL treat `docs/open-work.md` as the sole incomplete-work checklist.  
  - `EvidenceStage:` Observed (process rule)
- **[Ubiquitous]** Every architectural component SHALL maintain an explicit `SYSTEM.md` contract under `docs/architecture/`.  
  - `EvidenceStage:` Observed
- **[Event-driven]** WHEN a spec node exceeds the bloat threshold (~150 lines or >3 separable responsibilities) THE SYSTEM SHALL trigger file-to-folder expansion via the Reconciler.  
  - `EvidenceStage:` Sampled (policy; automation OW-02)
- **[Conditional]** IF a committed source file has no parent architecture node THEN THE SYSTEM SHALL fail the AST Gatekeeper / pre-commit path.  
  - `EvidenceStage:` Sampled (automation OW-04)
- **[Conditional]** IF only L4 model-judge evidence is available THEN THE SYSTEM SHALL NOT authorize merge on that evidence alone.  
  - `EvidenceStage:` Inferred (research foundation §5)

## 5. Architectural Decisions (ADRs)

- **ADR-001:** Five L1 components (Spec Engine, Reconciler, Wayfinder Connector, AST Gatekeeper, Measurement Harness).  
  - Impact: Measurement Harness is first-class, not an afterthought of “tests green.”
- **ADR-002:** Dual back-channels (structural + empirical) and dual-loop agent separation are orthogonal axes (process dual-backchannel-loop).  
- **ADR-003:** Directory names are kebab-case; contract file is always `SYSTEM.md`.  
- **ADR-004:** Research expansions require citable sources in `docs/research/foundation.md`; no placeholder citations.

## 6. Recursive expansion rule

Decompose a node **only when** subcomponents have independent interface seams (inputs/outputs that can change without rewriting siblings). Expand research narrative **only** with citations in the research foundation. Prefer deepening interfaces over lengthening prose.

## 7. Non-leaf note

L0 is not an atomic leaf. Implementation proceeds via L1 leaves and Wayfinder tickets OW-01…OW-05.
