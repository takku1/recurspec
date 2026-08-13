# Context Packer (L2)

<!-- recurspec-contract: 1.0 -->

## 1. System Intent & Responsibility

Assemble the smallest packet that lets a worker complete one loop turn on one node, and
refuse when that packet will not fit the budget.

**Does not own:** node state or caching (job-store), worker execution (worker-pool), or
the correctness of the spec a worker produces (Contract Engine).

## 2. Sub-System Decomposition

**Atomic leaf (atomic build).** One module, one test seam, one TDD session.

## 3. Interface Contracts

- **Inputs:** `node_id`; `max_tokens_per_node`; `survey_result`; the tree index; phase
  (frame | resolve | specify).
- **Outputs:** `packet` — contract card, parent §1+§3, sibling §3 index, own current
  draft, cached survey; a token estimate; or a `budget_overflow` refusal naming the
  oversized part.
- **Interface syntax:** `node_id` and `survey_result` come from job-store's outputs (see
  [job-store/SYSTEM.md](../job-store/SYSTEM.md) §3); `max_tokens_per_node` comes from
  Spec Runner's own input boundary (see [spec-runner/SYSTEM.md](../SYSTEM.md) §3). `packet`
  is consumed by worker-pool (see [worker-pool/SYSTEM.md](../worker-pool/SYSTEM.md) §3).
  The tree index and phase stay prose.

The packet is the entire abstraction barrier. If a worker needs something absent from it,
that is a missing interface contract in the tree, not a reason to widen the packet.

## 4. Invariants (EARS + Epistemic Stage)

- **[Ubiquitous]** The Packer SHALL include a node's parent §1 and §3 and its siblings'
  §3, and SHALL NOT include ancestors above the parent or any uncle subtree. (design
  intent; `test_pack_includes_parent_context_but_never_the_grandparent`)
  - `EvidenceStage:` Sampled
- **[Ubiquitous]** The Packer SHALL include sibling **interfaces only** (§3), never
  sibling bodies — packet size is then linear in sibling count, not sibling depth.
  (`test_pack_includes_sibling_interfaces_but_never_sibling_bodies`)
  - `EvidenceStage:` Sampled
- **[Conditional]** IF the estimated packet exceeds `max_tokens_per_node` THEN THE SYSTEM
  SHALL return `budget_overflow` naming the largest contributor and SHALL NOT truncate,
  summarize, or drop a section to fit. (refuse rather than guess;
  `test_pack_refuses_with_budget_overflow_rather_than_truncate`)
  - `EvidenceStage:` Sampled
- **[Conditional]** IF a validation is expressible as a schema assertion THEN THE PACKER
  SHALL run it before dispatch and SHALL NOT dispatch a node that already fails it.
  (today this is whole-tree validity via `build_tree_index`, not yet a narrower
  two-child-minimum/§8-completeness check scoped to just the target node - see Open
  work below; `test_pack_returns_schema_rejected_instead_of_dispatching_an_invalid_tree`)
  - `EvidenceStage:` Sampled
- **[Ubiquitous]** The Packer SHALL emit the contract card as the packet's leading bytes,
  byte-identical across nodes, so it forms a cacheable shared prefix.
  (`test_contract_card_is_byte_identical_across_two_different_nodes`)
  - `EvidenceStage:` Sampled

## 5. Architectural Decisions (ADRs)

- **ADR-001:** Token estimation is approximate and must be *conservative* — an
  underestimate that lets an oversized packet through defeats the budget. Estimate high.
- **ADR-002:** `budget_overflow` is routed to the Contract Reconciler as a bloat signal, not
  retried. A node whose neighbourhood does not fit is telling you it should be split.
- **ADR-003:** The contract card is generated from `src/recurspec/skill/references/design.md`, not
  maintained separately — a hand-kept card drifts from the skill it summarizes.

## 6. Leaf Execution & Test Seam

- **Implementation:** `src/recurspec/spec_runner/context_packer.py` — nested under the
  `spec_runner` subpackage shared with its two siblings (job-store, worker-pool).
- **Tests:** `tests/test_context_packer.py` (7 tests) — no ancestor above parent leaks
  in; sibling bodies excluded; overflow refuses rather than truncates; card is
  byte-identical across two different nodes; schema pre-check rejects before dispatch;
  unknown node_id raises rather than silently packing nothing; token estimate is
  conservative and zero for empty text.
- **Selected behavior:** token estimation uses a fixed conservative chars-per-token
  heuristic (`CHARS_PER_TOKEN = 3`). Exact vendor counting would add a dependency without
  changing the refusal seam. The schema pre-check intentionally validates the whole tree;
  narrowing it remains unnecessary unless measurement shows a material cost.

## 7. Measurement Seams

- **Primary metric:** `tokens_per_node_p95` (direction `lower`) — the number this whole
  subsystem exists to move
- **Secondary:** `packet_overflow_rate` (direction `lower`; a rise means nodes are being
  framed too broadly); `card_prefix_stability` (direction `higher`, target 1.0)
- **Evaluation Gate:** `modules/context-packer/measure.sh`
- **Backpressure:** `modules/context-packer/checks.sh`
- **Telemetry:** per-node `{phase, est_tokens, actual_tokens, sections_included, overflow}`
- **Branching:** worktree candidate; keep only on checks pass ∧ no `tokens_per_node_p95`
  regression ∧ no telemetry contradiction

## 8. Technology Resolution

- **Decision class:** BUILD
- **Justification:** *Differentiator + fatal fit gap.* The packet is defined in terms of
  Recurspec's own §1–§8 contract shape and its bounded-neighbour rule. No third party models
  that structure, and this is precisely where token cost is won or lost.
- **Selected:** Python module in `src/recurspec/spec_runner/`; token estimation is
  currently a fixed conservative chars-per-token heuristic (3 chars/token, biased high).
- **Standard / protocol:** none — internal
- **Alternatives considered:**
  | Option | Why not |
  |--------|---------|
  | RAG / vector retrieval over the tree | Retrieval is for when you don't know what's relevant. Here the relevant set is *exactly determined* by tree position — embedding it would add latency, cost, and non-determinism to a lookup that is already O(1) |
  | Generic prompt-template libraries | Solve interpolation, not budgeting or neighbour-scoping — the two things that matter here |
  | Let each worker read files itself | This is the naive baseline being replaced: unbounded reads, no budget, no cacheable prefix |
- **Fit gap:** n/a (custom by intent)
- **Seam:** `src/recurspec/spec_runner/context_packer.py` — workers receive packets, never paths
- **Exit cost:** n/a
- **Cost model:** our engineering time; expected to *reduce* per-run inference spend
- **Liability transferred:** none
- **Operational owner:** us
- **Failure mode:** a packer bug either over-packs (budget blown, silently expensive) or
  under-packs (worker specs a node blind). The `sections_included` telemetry field exists
  to make the second case detectable rather than invisible.
- **Open questions:** none. Re-open the whole-tree pre-check only if measured profiling
  shows it is a material cost.
