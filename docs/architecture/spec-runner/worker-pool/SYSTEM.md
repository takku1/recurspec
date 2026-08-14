# Worker Pool (L2)

<!-- recurspec-contract: 1.0 -->

## 1. System Intent & Responsibility

Run one node's loop turn in an isolated agent session, given a packet, and return a
structured result — concurrently, with retries and a hard per-node budget.

**Does not own:** what the worker is allowed to see (context-packer), what counts as a
correct answer (Contract Engine / Stack Resolver), or run state (job-store).

## 2. Sub-System Decomposition

**Atomic leaf (procured).** Resolved ADOPT uniformly — we spec the seam, not the agent
runtime's internals. Per the termination guarantee, this subtree stops here: we do not
decompose tool-use loops, retry backoff, or streaming.

## 3. Interface Contracts

- **Inputs:** `packet`; `max_tokens_per_node`; `concurrency`; phase; model tier.
- **Outputs:** Structured result — child frames, or a decision class + §8 draft, or a
  full node body; plus actual token/latency counts; or a typed failure (budget_exceeded,
  tool_error, refused). A successful independent CHECK may persist merge authorization
  state for the Evaluation Gate.
- **Interface syntax:** `packet` comes from context-packer's output (see
  [context-packer/SYSTEM.md](../context-packer/SYSTEM.md) §3); `max_tokens_per_node` and
  `concurrency` come from Spec Runner's own input boundary (see
  [spec-runner/SYSTEM.md](../SYSTEM.md) §3). The structured result has no declared
  consumer elsewhere in the tree yet, so it stays prose rather than a port — the Runner's
  own write-back into job-store is real but not yet specified at that level of detail.

Workers are **stateless between nodes**. Anything a worker needed to know is in its
packet, and anything it learned is in its result.

## 4. Invariants (EARS + Epistemic Stage)

- **[Ubiquitous]** A worker SHALL receive a packet and SHALL NOT read the tree directly.
  (the packet is the only abstraction barrier that makes per-node cost bounded; a worker
  that can open files can defeat every budget; the adapter's own call signature is
  structurally incapable of forwarding a tree_root or path -
  `test_worker_only_ever_receives_the_packet_never_a_filesystem_path` - though full
  runtime-level filesystem sandboxing is the injected runtime's own responsibility, not
  something this adapter controls once a real agent runtime is plugged in)
  - `EvidenceStage:` Sampled
- **[Ubiquitous]** The pool SHALL route mechanical phases (FRAME, structural checks) to
  the cheap tier and RESOLVE to the capable tier.
  (`test_tier_for_phase_routes_mechanical_cheap_and_resolve_capable`)
  - `EvidenceStage:` Sampled
- **[Conditional]** IF a worker's spend reaches `max_tokens_per_node` THEN THE SYSTEM
  SHALL abort that worker and record `budget_exceeded`, and SHALL NOT return a partial
  spec as if complete. (refuse rather than guess;
  `test_budget_exceeded_discards_the_body_rather_than_return_a_partial_node`)
  - `EvidenceStage:` Sampled
- **[Conditional]** IF a worker produced the node under review THEN THE SYSTEM SHALL NOT
  assign that worker its `[BRANCH]`/`[ATOMIC]` check. (maker ≠ checker,
  [Recurspec](../../../../src/recurspec/skill/SKILL.md) — a decomposer grading its own
  termination call is the failure mode this rule exists for;
  `test_maker_cannot_check_the_node_it_produced`)
  - `EvidenceStage:` Sampled
- **[State-driven]** WHILE sibling nodes are independent THE SYSTEM SHALL be permitted to
  execute them concurrently up to the configured limit.
  (`test_concurrency_cap_is_never_exceeded`, timing-based, run repeatedly to rule out
  flakiness)
  - `EvidenceStage:` Sampled

## 5. Architectural Decisions (ADRs)

- **ADR-001:** Sibling fan-out is bounded by a configured limit, not by tree breadth. An
  unbounded swarm on a wide node is how a run becomes expensive without becoming faster.
- **ADR-002:** Concurrency is a **latency** decision (parent ADR-006). It is recorded here
  so nobody tunes it expecting a smaller bill.
- **ADR-003:** Results are structured, not prose. The pool returns fields the Contract Engine
  can validate; free-text answers would need a model call to parse — paying twice.

## 6. Leaf Execution & Test Seam

- **Implementation:** `src/recurspec/spec_runner/workers.py` — same `spec_runner`
  subpackage as context-packer and job-store. Implements the pool's own policy (budget,
  tier routing, maker ≠ checker, concurrency cap) against an injected `RuntimeCall`; does
  not ship a concrete agent-runtime integration (see §8 - the SDK pin is still
  unverified, deliberately not asserted).
- **Tests:** `tests/test_worker_pool.py` (17 tests) — worker cannot reach the filesystem
  outside its packet; budget abort yields `budget_exceeded` not a partial node; maker ≠
  checker enforced on the atomicity call; concurrency cap respected (timing-based, run
  repeatedly to rule out flakiness); tier routing; invalid concurrency rejected;
  authorization persistence is single-writer so a later unrelated `dispatch()` cannot
  drop a prior Candidate identity
  (`test_persisted_candidate_identity_survives_a_later_unrelated_dispatch`).
- **Runtime adapter:** the module's policy is complete and tested against a fake adapter;
  the primary-source-verified production adapter is tracked only as ROADMAP R-204.
- **Authorization seam:** `WorkerPool` persists maker/checker state only after successful
  within-budget produce and independent CHECK turns, then binds authorization to one
  Candidate branch and commit; `load_merge_authorization()` refuses incomplete records.
  (`test_completed_independent_check_persists_merge_authorization`,
  `test_budget_rejected_producer_cannot_establish_merge_authorization`)

## 7. Measurement Seams

- **Primary metric:** `wall_clock_per_node_p95` (direction `lower`)
- **Secondary:** `worker_retry_rate` (direction `lower`); `tier_misroute_rate` — RESOLVE
  turns that ran on the cheap tier (direction `lower`, target 0)
- **Evaluation Gate:** `modules/worker-pool/measure.sh`
- **Backpressure:** `modules/worker-pool/checks.sh`
- **Telemetry:** per-worker `{node_id, phase, tier, tokens_in, tokens_out, ms, outcome}`
- **Branching:** worktree candidate; keep only on checks pass ∧ no latency regression ∧
  no telemetry contradiction

## 8. Technology Resolution

- **Decision class:** BUILD
- **Justification:** The implemented value is Recurspec-specific dispatch policy: bounded
  concurrency, phase routing, budget refusal, and maker/checker state. A concrete runtime
  is intentionally outside this leaf until R-204 resolves it from primary sources.
- **Selected:** Python `WorkerPool` over an injected `RuntimeCall` protocol.
- **Standard / protocol:** internal immutable dataclasses; MCP may be selected by the
  future runtime adapter but is not asserted here.
- **Alternatives considered:**
  | Option | Why not |
  |--------|---------|
  | LangGraph | Owns graph state and control flow — precisely what job-store and the Runner own here. Adopting it would mean two schedulers disagreeing about which node is ready |
  | CrewAI / AutoGen | Role and conversation abstractions add a layer we do not need; a worker here is a stateless function from packet to result |
  | Raw HTTP against the model API | Cheapest to start, then rebuilds tool-use, retry, and session isolation by hand — the classic BUILD that fails the commodity test |
  | Bare threads calling a completion endpoint | No tool use, so RESEARCH cannot run inside a worker |
- **Fit gap:** no concrete production agent-runtime adapter is shipped; R-204 owns that
  separately resolved integration.
- **Seam:** `src/recurspec/spec_runner/workers.py`; the Runner sees
  `WorkerPool.dispatch(node_id, packet, phase, worker_id, max_tokens_per_node) -> WorkerResult`
- **Exit cost:** LOW — runtime integrations implement one injected call protocol; pool
  policy, packets, and stored state remain unchanged.
- **Cost model:** local policy has no service spend; runtime inference cost remains
  unresolved under R-204.
- **Liability transferred:** none until a runtime is selected.
- **Operational owner:** us.
- **Failure mode:** an injected runtime error returns `tool_error`; absence of a production
  adapter prevents production dispatch rather than guessing an integration.
- **Open questions:** none outside ROADMAP R-204.
