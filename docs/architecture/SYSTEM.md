# Recurspec Engine (L0)

<!-- recurspec-contract: 1.0 -->

## 1. System Intent & Responsibility

Recurspec is a research-informed contract and evaluation system for AI-assisted software
engineering. It advances one finite, evidence-backed transition through an internal
`DISCOVER -> RESOLVE -> EXECUTE -> CHECK -> RECONCILE` loop. It keeps the Contract Tree,
implementation evidence, and `ROADMAP.md` consistent without allowing derived state to
replace any of them. This is the tree root.

**Does not own:** product application code of consumer repos; those *use* Recurspec process and may mirror this tree shape.

Process (not code modules): [contract-design](../process/contract-design.md), [stack-resolution](../process/stack-resolution.md), [evidence-cycle](../process/evidence-cycle.md), [contract-reconciliation](../process/contract-reconciliation.md).
Incomplete work: [ROADMAP.md](../../ROADMAP.md).
Research: [research/foundations.md](../research/foundations.md).

## 2. Sub-System Decomposition

| Module | Path | Responsibility |
|-----------|------|----------------|
| Contract Engine | [contract-engine/SYSTEM.md](./contract-engine/SYSTEM.md) | Create/validate EARS `SYSTEM.md` trees |
| Stack Resolver | [stack-resolver/SYSTEM.md](./stack-resolver/SYSTEM.md) | Decision class per node; third-party-first gate; recursion stopping rule |
| Spec Runner | [spec-runner/SYSTEM.md](./spec-runner/SYSTEM.md) | Executes the loop: scheduling, context budgeting, incremental re-walk |
| Contract Reconciler | [contract-reconciler/SYSTEM.md](./contract-reconciler/SYSTEM.md) | Structural sensory signals; auto-expand |
| Frontier Adapter | [frontier-adapter/SYSTEM.md](./frontier-adapter/SYSTEM.md) | Leaf → frontier tickets |
| Structure Gate | [structure-gate/SYSTEM.md](./structure-gate/SYSTEM.md) | Deterministic zero-drift / coverage checks |
| Evaluation Gate | [evaluation-gate/SYSTEM.md](./evaluation-gate/SYSTEM.md) | Branching measure; Empirical Feedback inputs |

## 3. Interface Contracts

- **Inputs:** `contract_path`; `max_tokens_per_node`; `concurrency`; product vision / NL scope; git diffs; existing code ASTs; measure baselines.
- **Outputs:** Contract Tree changes; one safe next route; common read-only check reports;
  Research Frontier tickets; Candidate decisions; reconciliation drafts; baseline logs
  under `.recurspec/evidence/`.
- **Common CLI:** `recurspec status`, `recurspec check`, `recurspec evaluate`,
  `recurspec reconcile plan`, and `recurspec skills`. Specialized command families remain
  compatibility and research interfaces rather than the onboarding vocabulary.
- **Interface syntax:** these three ports are declared this level down because a real child already consumes each by that exact name: `contract_path` by Contract Engine (see [contract-engine/SYSTEM.md](./contract-engine/SYSTEM.md) §3), `max_tokens_per_node` and `concurrency` by Spec Runner and its own children (see [spec-runner/SYSTEM.md](./spec-runner/SYSTEM.md) §3). The other L1 modules (Stack Resolver, Contract Reconciler, Frontier Adapter, Structure Gate, Evaluation Gate) are independently invoked CLI gates with no cross-sibling data flow to formalize as ports; the historical R-105 finding remains in [CHANGELOG.md](../../CHANGELOG.md) and git.

## 4. Invariants (EARS + Epistemic Stage)

- **[Ubiquitous]** The Root System SHALL treat `ROADMAP.md` as the sole incomplete-work registry. (process rule)
  - `EvidenceStage:` Unknown
- **[Ubiquitous]** Every architectural module SHALL maintain an explicit `SYSTEM.md` contract under `docs/architecture/`.
  - `EvidenceStage:` Unknown
- **[Event-driven]** WHEN a Contract Node exceeds the 150-line bloat threshold THE SYSTEM
  SHALL emit a Contract Reconciler split-review action; Architect review decides the
  interface-driven expansion. (`test_reconciler_proposes_review_for_bloat_and_uncontracted_test_seams`)
  - `EvidenceStage:` Sampled
- **[Conditional]** IF a committed source file has no parent Contract Node THEN THE
  SYSTEM SHALL fail the Structure Gate. (`test_structure_gate_reports_each_public_symbol_in_an_uncontracted_source_file`)
  - `EvidenceStage:` Sampled
- **[Conditional]** IF only L4 model-judge evidence is available THEN THE SYSTEM SHALL NOT authorize merge on that evidence alone. (research foundation §5)
  - `EvidenceStage:` Unknown
- **[Ubiquitous]** Every node SHALL carry a decision class before it is decomposed or specified; every terminal node SHALL carry a complete §8 Technology Resolution block. (`test_resolution_audit_reports_incomplete_fields_and_refuses_vendor_on_defer`)
  - `EvidenceStage:` Sampled
- **[Conditional]** IF a node resolves to BUY or ADOPT THEN THE SYSTEM SHALL treat it as terminal and SHALL NOT decompose the vendor's internals. (recursion termination guarantee)
  - `EvidenceStage:` Unknown
- **[Event-driven]** WHEN the common read-only check runs THE SYSTEM SHALL preserve each
  checker's typed details and evidence license while reporting them through one Finding
  envelope. (`test_check_cli_aggregates_selected_read_only_checks`)
  - `EvidenceStage:` Sampled
- **[Conditional]** IF Coverage Review proposes a missing Contract Node or cross-node
  relationship THEN THE SYSTEM SHALL label it `Unknown` or `Inferred` and SHALL require
  Architect review before changing the Contract Tree. (design policy)
  - `EvidenceStage:` Unknown

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
- **ADR-007:** The common interface is smaller than the implementation architecture.
  `status`, a consolidated read-only `check`, explicit `evaluate`, draft-only
  `reconcile plan`, and `skills` form the ordinary path. Existing narrow commands remain
  compatibility or research tools until the common interface preserves their refusal
  guarantees. Interface compression never compresses mutation authority.

## 6. Recursive expansion rule

- **Package implementation glue:** `src/recurspec/__init__.py`,
  `src/recurspec/__main__.py`, `src/recurspec/inspection.py`,
  `src/recurspec/fanout.py`, `src/recurspec/study.py`.
- **Test Surface Seam:** `tests/test_repository.py`, `tests/test_skill_references.py`,
  `tests/test_fanout.py`, `tests/test_study.py`, `tests/test_inspection.py`.

Resolve before decomposing. Decompose a node **only when** either its parts would resolve to *different* decision classes (split at that fault line), or it is uniformly BUILD and too large for one TDD session (split by independent interface seam — inputs/outputs that can change without rewriting siblings). Stop at procurement boundaries and at one-session build units. Full rule with depth guards: [contract-design.md](../process/contract-design.md).

Expand research narrative **only** with citations in the research foundation. Prefer deepening interfaces over lengthening prose.

## 7. Non-leaf note

L0 is not an atomic leaf. Incomplete implementation is tracked only in `ROADMAP.md`.
