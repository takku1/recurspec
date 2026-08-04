# Recursive System Specification Engine (L0 Root)

## 1. System Intent & Responsibility

RSS is a **self-healing, multi-signal specification engine** for AI-assisted software engineering. It maintains a fractal tree of machine-usable contracts (`SYSTEM.md`), executes work through Wayfinder frontiers, and closes the loop with dual back-channels (structural + empirical) under an SDB verification gate.

**Does not own:** product application code of consumer repos; those *use* RSS process and may mirror this tree shape.

## 2. Sub-System Decomposition

| Component | Path | Responsibility |
|-----------|------|----------------|
| Spec Engine | [spec-engine/SYSTEM.md](./spec-engine/SYSTEM.md) | Create/validate EARS `SYSTEM.md` trees |
| Technology Resolver | [technology-resolver/SYSTEM.md](./technology-resolver/SYSTEM.md) | Decision class per node; third-party-first gate; recursion stopping rule |
| Reconciler | [reconciler/SYSTEM.md](./reconciler/SYSTEM.md) | Structural sensory signals; auto-expand |
| Wayfinder Connector | [wayfinder-connector/SYSTEM.md](./wayfinder-connector/SYSTEM.md) | Leaf → frontier tickets |
| AST Gatekeeper | [ast-gatekeeper/SYSTEM.md](./ast-gatekeeper/SYSTEM.md) | Deterministic zero-drift / coverage checks |
| Measurement Harness | [measurement-harness/SYSTEM.md](./measurement-harness/SYSTEM.md) | Branching measure; Back-Channel B inputs |

Process (not code modules): [decomposition-loop](../process/decomposition-loop.md), [technology-resolution](../process/technology-resolution.md), [dual-backchannel-loop](../process/dual-backchannel-loop.md), [multi-signal-reconciler](../process/multi-signal-reconciler.md).  
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
- **[Ubiquitous]** Every node SHALL carry a decision class before it is decomposed or specified; every terminal node SHALL carry a §8 Technology Resolution block.  
  - `EvidenceStage:` Observed (process rule; automation OW-06)
- **[Conditional]** IF a node resolves to BUY or ADOPT THEN THE SYSTEM SHALL treat it as terminal and SHALL NOT decompose the vendor's internals.  
  - `EvidenceStage:` Observed (recursion termination guarantee)

## 5. Architectural Decisions (ADRs)

- **ADR-001:** ~~Five L1 components~~ **Superseded by ADR-005.**  
  - Original: Spec Engine, Reconciler, Wayfinder Connector, AST Gatekeeper, Measurement Harness.  
  - Impact retained: Measurement Harness is first-class, not an afterthought of “tests green.”
- **ADR-002:** Dual back-channels (structural + empirical) and dual-loop agent separation are orthogonal axes (process dual-backchannel-loop).  
- **ADR-003:** Directory names are kebab-case; contract file is always `SYSTEM.md`.  
- **ADR-004:** Research expansions require citable sources in `docs/research/foundation.md`; no placeholder citations.
- **ADR-005:** **Six L1 components** — adds Technology Resolver.  
  - *Context:* the tree could decompose indefinitely with no rule for when to stop, and nothing biased a node toward existing solutions. Both defects have the same root: no node was ever asked *what will implement this?* before being asked *what are its parts?*  
  - *Decision:* resolution precedes decomposition. A node's decision class both selects its technology and determines whether it terminates.  
  - *Impact:* recursion gains a floor (procurement boundary); "reinvent the wheel" becomes a gate failure rather than a review comment; leaf specs carry a real stack instead of a topic name.

## 6. Recursive expansion rule

Resolve before decomposing. Decompose a node **only when** either its parts would resolve to *different* decision classes (split at that fault line), or it is uniformly BUILD and too large for one TDD session (split by independent interface seam — inputs/outputs that can change without rewriting siblings). Stop at procurement boundaries and at one-session build units. Full rule with depth guards: [decomposition-loop.md](../process/decomposition-loop.md).

Expand research narrative **only** with citations in the research foundation. Prefer deepening interfaces over lengthening prose.

## 7. Non-leaf note

L0 is not an atomic leaf. Implementation proceeds via L1 leaves and Wayfinder tickets OW-01…OW-05.
