# Context Packer (L2)

## 1. System Intent & Responsibility

Assemble the smallest packet that lets a worker complete one loop turn on one node, and
refuse when that packet will not fit the budget.

**Does not own:** node state or caching (job-store), worker execution (worker-pool), or
the correctness of the spec a worker produces (Spec Engine).

## 2. Sub-System Decomposition

**Atomic leaf (atomic build).** One module, one test seam, one TDD session.

## 3. Interface Contracts

| | |
|--|--|
| **Inputs** | `node_id`; the tree index; `max_tokens_per_node`; phase (`frame` \| `resolve` \| `specify`); cached survey rows for this node's capability |
| **Outputs** | A packet — contract card, parent §1+§3, sibling §3 index, own current draft, cached survey; a token estimate; **or** a `budget_overflow` refusal naming the oversized part |

The packet is the entire abstraction barrier. If a worker needs something absent from it,
that is a missing interface contract in the tree, not a reason to widen the packet.

## 4. Invariants (EARS + Epistemic Stage)

- **[Ubiquitous]** The Packer SHALL include a node's parent §1 and §3 and its siblings'
  §3, and SHALL NOT include ancestors above the parent or any uncle subtree.
  - `EvidenceStage:` Unknown · design intent
- **[Ubiquitous]** The Packer SHALL include sibling **interfaces only** (§3), never
  sibling bodies — packet size is then linear in sibling count, not sibling depth.
  - `EvidenceStage:` Unknown
- **[Conditional]** IF the estimated packet exceeds `max_tokens_per_node` THEN THE SYSTEM
  SHALL return `budget_overflow` naming the largest contributor and SHALL NOT truncate,
  summarize, or drop a section to fit.
  - `EvidenceStage:` Unknown — refuse rather than guess
- **[Conditional]** IF a validation is expressible as a schema assertion THEN THE PACKER
  SHALL run it before dispatch and SHALL NOT dispatch a node that already fails it.
  - `EvidenceStage:` Unknown — catches two-child-minimum and §8-completeness violations
    for zero tokens instead of one model call plus a rejected result
- **[Ubiquitous]** The Packer SHALL emit the contract card as the packet's leading bytes,
  byte-identical across nodes, so it forms a cacheable shared prefix.
  - `EvidenceStage:` Unknown · OW-44

## 5. Architectural Decisions (ADRs)

- **ADR-001:** Token estimation is approximate and must be *conservative* — an
  underestimate that lets an oversized packet through defeats the budget. Estimate high.
- **ADR-002:** `budget_overflow` is routed to the Reconciler as a bloat signal, not
  retried. A node whose neighbourhood does not fit is telling you it should be split.
- **ADR-003:** The contract card is generated from `recursive-spec/SKILL.md`, not
  maintained separately — a hand-kept card drifts from the skill it summarizes.

## 6. Leaf Execution & Test Seam

- **Implementation:** `src/spec_runner/context_packer.py`
- **Tests:** `tests/test_context_packer.py` — must cover: no ancestor above parent leaks
  in; sibling bodies excluded; overflow refuses rather than truncates; card is
  byte-identical across two different nodes; schema pre-check rejects before dispatch
- **Open work:** OW-42

## 7. Measurement Seams

- **Primary metric:** `tokens_per_node_p95` (direction `lower`) — the number this whole
  subsystem exists to move
- **Secondary:** `packet_overflow_rate` (direction `lower`; a rise means nodes are being
  framed too broadly); `card_prefix_stability` (direction `higher`, target 1.0)
- **Harness:** `components/context-packer/measure.sh`
- **Backpressure:** `components/context-packer/checks.sh`
- **Telemetry:** per-node `{phase, est_tokens, actual_tokens, sections_included, overflow}`
- **Branching:** worktree hypothesis; keep only on checks pass ∧ no `tokens_per_node_p95`
  regression ∧ no telemetry contradiction

## 8. Technology Resolution

- **Decision class:** BUILD
- **Justification:** *Differentiator + fatal fit gap.* The packet is defined in terms of
  RSS's own §1–§8 contract shape and its bounded-neighbour rule. No third party models
  that structure, and this is precisely where token cost is won or lost.
- **Selected:** Python module in `src/spec_runner/`; token estimation via the vendor's
  published counting endpoint where available, else a conservative local heuristic
- **Standard / protocol:** none — internal
- **Alternatives considered:**
  | Option | Why not |
  |--------|---------|
  | RAG / vector retrieval over the tree | Retrieval is for when you don't know what's relevant. Here the relevant set is *exactly determined* by tree position — embedding it would add latency, cost, and non-determinism to a lookup that is already O(1) |
  | Generic prompt-template libraries | Solve interpolation, not budgeting or neighbour-scoping — the two things that matter here |
  | Let each worker read files itself | This is the naive baseline being replaced: unbounded reads, no budget, no cacheable prefix |
- **Fit gap:** n/a (custom by intent)
- **Seam:** `src/spec_runner/context_packer.py` — workers receive packets, never paths
- **Exit cost:** n/a
- **Cost model:** our engineering time; expected to *reduce* per-run inference spend
- **Liability transferred:** none
- **Operational owner:** us
- **Failure mode:** a packer bug either over-packs (budget blown, silently expensive) or
  under-packs (worker specs a node blind). The `sections_included` telemetry field exists
  to make the second case detectable rather than invisible.
- **Open questions:** OW-42, OW-44
