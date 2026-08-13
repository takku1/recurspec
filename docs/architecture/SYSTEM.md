# Recurspec Engine (L0 Root)

## 1. System Intent & Responsibility

Recurspec is a research-informed contract and evaluation system for AI-assisted software engineering. It maintains a Contract Tree of machine-usable `SYSTEM.md` nodes, executes work through Research Frontiers, and reconciles Structural and Empirical Feedback under a deterministic verification gate.

**Does not own:** product application code of consumer repos; those *use* Recurspec process and may mirror this tree shape.

## 2. Sub-System Decomposition

| Module | Path | Responsibility |
|-----------|------|----------------|
| Contract Engine | [contract-engine/SYSTEM.md](./contract-engine/SYSTEM.md) | Create/validate EARS `SYSTEM.md` trees |
| Stack Resolver | [stack-resolver/SYSTEM.md](./stack-resolver/SYSTEM.md) | Decision class per node; third-party-first gate; recursion stopping rule |
| Spec Runner | [design-runner/SYSTEM.md](./design-runner/SYSTEM.md) | Executes the loop: scheduling, context budgeting, incremental re-walk |
| Contract Reconciler | [contract-reconciler/SYSTEM.md](./contract-reconciler/SYSTEM.md) | Structural sensory signals; auto-expand |
| Frontier Adapter | [frontier-adapter/SYSTEM.md](./frontier-adapter/SYSTEM.md) | Leaf → frontier tickets |
| Structure Gate | [structure-gate/SYSTEM.md](./structure-gate/SYSTEM.md) | Deterministic zero-drift / coverage checks |
| Evaluation Gate | [evaluation-gate/SYSTEM.md](./evaluation-gate/SYSTEM.md) | Branching measure; Empirical Feedback inputs |

Process (not code modules): [contract-design](../process/contract-design.md), [stack-resolution](../process/stack-resolution.md), [evidence-cycle](../process/evidence-cycle.md), [contract-reconciliation](../process/contract-reconciliation.md).
Incomplete work: [ROADMAP.md](../../ROADMAP.md).
Research: [research/foundations.md](../research/foundations.md).

## 3. Interface Contracts

| Direction | Artifacts |
|-----------|-----------|
| **Inputs** | Product vision / NL scope; git diffs; existing code ASTs; measure baselines |
| **Outputs** | Fractal `docs/architecture/**/SYSTEM.md`; Wayfinder tickets; pass/fail gate reports; baseline logs under `.recurspec/evidence/` |

## 4. Invariants (EARS + Epistemic Stage)

- **[Ubiquitous]** The Root System SHALL treat `ROADMAP.md` as the sole incomplete-work registry.
  - `EvidenceStage:` Asserted (process rule)
- **[Ubiquitous]** Every architectural module SHALL maintain an explicit `SYSTEM.md` contract under `docs/architecture/`.
  - `EvidenceStage:` Asserted
- **[Event-driven]** WHEN a spec node exceeds the bloat threshold (~150 lines or >3 separable responsibilities) THE SYSTEM SHALL trigger file-to-folder expansion via the Contract Reconciler.
  - `EvidenceStage:` Asserted (policy; automation OW-02)
- **[Conditional]** IF a committed source file has no parent architecture node THEN THE SYSTEM SHALL fail the Structure Gate / pre-commit path.
  - `EvidenceStage:` Asserted (automation OW-04)
- **[Conditional]** IF only L4 model-judge evidence is available THEN THE SYSTEM SHALL NOT authorize merge on that evidence alone.
  - `EvidenceStage:` Asserted (research foundation §5)
- **[Ubiquitous]** Every node SHALL carry a decision class before it is decomposed or specified; every terminal node SHALL carry a §8 Technology Resolution block.
  - `EvidenceStage:` Asserted (process rule; automation OW-06)
- **[Conditional]** IF a node resolves to BUY or ADOPT THEN THE SYSTEM SHALL treat it as terminal and SHALL NOT decompose the vendor's internals.
  - `EvidenceStage:` Asserted (recursion termination guarantee)

## 5. Architectural Decisions (ADRs)

- **ADR-001:** ~~Five L1 modules~~ **Superseded by ADR-005.**
  - Original: Contract Engine, Contract Reconciler, Frontier Adapter, Structure Gate, Evaluation Gate.
  - Impact retained: Evaluation Gate is first-class, not an afterthought of “tests green.”
- **ADR-002:** Structural and Empirical Feedback and maker-checker separation are orthogonal axes (see the evidence cycle).
- **ADR-003:** Directory names are kebab-case; contract file is always `SYSTEM.md`.
- **ADR-004:** Research expansions require citable sources in `docs/research/foundations.md`; no placeholder citations.
- **ADR-005:** **Six L1 modules** — adds Stack Resolver.
  - *Context:* the tree could decompose indefinitely with no rule for when to stop, and nothing biased a node toward existing solutions. Both defects have the same root: no node was ever asked *what will implement this?* before being asked *what are its parts?*
  - *Decision:* resolution precedes decomposition. A node's decision class both selects its technology and determines whether it terminates.
  - *Impact:* recursion gains a floor (procurement boundary); "reinvent the wheel" becomes a gate failure rather than a review comment; leaf specs carry a real stack instead of a topic name.
- **ADR-006:** **Seven L1 modules** — adds Spec Runner.
  - *Context:* the loop was fully specified as a process and entirely manual as an
    execution. Running it depth-first in one conversation makes cost grow with tree size,
    re-derives context at every node, and re-walks everything after any edit.
  - *Decision:* separate *judgment* from *scheduling*. The Runner decides what executes
    next and what that worker may see; it never decides what the answer is. Per-node
    context is bounded to the immediate neighbourhood, and re-walks are incremental on a
    contract-surface hash — a build system, not a crawler.
  - *Impact:* per-node cost becomes O(1) in tree size rather than O(depth × breadth);
    the tree becomes executable by parallel workers without a second source of truth,
    because the Runner's state is a regenerable cache and markdown stays sovereign.

## 6. Recursive expansion rule

Resolve before decomposing. Decompose a node **only when** either its parts would resolve to *different* decision classes (split at that fault line), or it is uniformly BUILD and too large for one TDD session (split by independent interface seam — inputs/outputs that can change without rewriting siblings). Stop at procurement boundaries and at one-session build units. Full rule with depth guards: [contract-design.md](../process/contract-design.md).

Expand research narrative **only** with citations in the research foundation. Prefer deepening interfaces over lengthening prose.

## 7. Non-leaf note

L0 is not an atomic leaf. Implementation proceeds via L1 leaves and Wayfinder tickets OW-01…OW-05.
