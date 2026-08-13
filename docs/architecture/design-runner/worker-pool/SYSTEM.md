# Worker Pool (L2)

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

| | |
|--|--|
| **Inputs** | A packet from context-packer; phase; model tier; `max_tokens_per_node`; concurrency limit |
| **Outputs** | Structured result — child frames, or a decision class + §8 draft, or a full node body; plus actual token/latency counts; or a typed failure (`budget_exceeded`, `tool_error`, `refused`) |

Workers are **stateless between nodes**. Anything a worker needed to know is in its
packet, and anything it learned is in its result.

## 4. Invariants (EARS + Epistemic Stage)

- **[Ubiquitous]** A worker SHALL receive a packet and SHALL NOT read the tree directly.
  - `EvidenceStage:` Asserted — the packet is the only abstraction barrier that makes
    per-node cost bounded; a worker that can open files can defeat every budget
- **[Ubiquitous]** The pool SHALL route mechanical phases (FRAME, structural checks) to
  the cheap tier and RESOLVE to the capable tier.
  - `EvidenceStage:` Asserted · OW-43
- **[Conditional]** IF a worker's spend reaches `max_tokens_per_node` THEN THE SYSTEM
  SHALL abort that worker and record `budget_exceeded`, and SHALL NOT return a partial
  spec as if complete.
  - `EvidenceStage:` Asserted — refuse rather than guess
- **[Conditional]** IF a worker produced the node under review THEN THE SYSTEM SHALL NOT
  assign that worker its `[BRANCH]`/`[ATOMIC]` check.
  - `EvidenceStage:` Asserted — maker ≠ checker ([Recurspec](../../../../src/recurspec/skill/SKILL.md));
    a decomposer grading its own termination call is the failure mode this rule exists for
- **[State-driven]** WHILE sibling nodes are independent THE SYSTEM MAY execute them
  concurrently up to the configured limit.
  - `EvidenceStage:` Asserted

## 5. Architectural Decisions (ADRs)

- **ADR-001:** Sibling fan-out is bounded by a configured limit, not by tree breadth. An
  unbounded swarm on a wide node is how a run becomes expensive without becoming faster.
- **ADR-002:** Concurrency is a **latency** decision (parent ADR-006). It is recorded here
  so nobody tunes it expecting a smaller bill.
- **ADR-003:** Results are structured, not prose. The pool returns fields the Contract Engine
  can validate; free-text answers would need a model call to parse — paying twice.

## 6. Leaf Execution & Test Seam

- **Implementation:** `src/spec_runner/workers.py` (adapter over the agent runtime)
- **Tests:** `tests/test_worker_pool.py` — must cover: worker cannot reach the filesystem
  outside its packet; budget abort yields `budget_exceeded` not a partial node; maker ≠
  checker enforced on the atomicity call; concurrency cap respected
- **Open work:** OW-43

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

- **Decision class:** ADOPT
- **Selected:** the Claude Agent SDK as the worker runtime — it already provides session
  isolation, tool use, retries, structured output, and concurrent sessions.
  - **Pin:** not recorded. Package name and version must be read from live documentation at
    implementation (OW-43); this spec does not assert a version it has not verified.
- **Standard / protocol:** MCP for any tools workers are granted
- **Alternatives considered:**
  | Option | Why not |
  |--------|---------|
  | LangGraph | Owns graph state and control flow — precisely what job-store and the Runner own here. Adopting it would mean two schedulers disagreeing about which node is ready |
  | CrewAI / AutoGen | Role and conversation abstractions add a layer we do not need; a worker here is a stateless function from packet to result |
  | Raw HTTP against the model API | Cheapest to start, then rebuilds tool-use, retry, and session isolation by hand — the classic BUILD that fails the commodity test |
  | Bare threads calling a completion endpoint | No tool use, so RESEARCH cannot run inside a worker |
- **Fit gap:** the SDK does not know Recurspec's phases, tiering policy, or budget rule. That gap
  is the thin adapter in `workers.py` — and it is the only custom code here.
- **Seam:** `src/spec_runner/workers.py`; the Runner sees `run(packet) -> Result`
- **Exit cost:** MEDIUM — swapping runtimes rewrites the adapter and the tool wiring, but
  no packet, store, or spec format changes. Contained by design.
- **Cost model:** per-token inference at the tier used. This is the dominant recurring cost
  of the whole system, which is why the parent's levers target it directly.
- **Liability transferred:** model hosting, tool sandboxing, retry semantics
- **Operational owner:** vendor (runtime) / us (adapter)
- **Failure mode:** runtime outage stalls the run; the job-store keeps claimed nodes
  recoverable so a restart resumes rather than re-walks.
- **Open questions:** OW-43 (pin + tier routing table)
