# Spec Runner (L1)

> Process: [decomposition-loop.md](../../process/decomposition-loop.md) ·
> Resolution gate: [technology-resolution.md](../../process/technology-resolution.md)

## 1. System Intent & Responsibility

Execute the decomposition loop over a tree of nodes: decide **what runs next**, **what
that worker is allowed to see**, and **what can be skipped**. Owns scheduling, context
budgeting, and incremental invalidation.

**Does not own:** the loop's judgment (Technology Resolver), contract structure or
validation (Spec Engine), ticket publication (Wayfinder Connector), or keep/revert
measurement (Measurement Harness). The Runner never decides *what the answer is* — only
which question is asked next and under what budget.

## 2. Sub-System Decomposition

Resolution is **not uniform** across the parts, so the node splits at the class fault
lines (decomposition-loop §4):

| Child | Class | Responsibility |
|-------|-------|----------------|
| [job-store](./job-store/SYSTEM.md) | ADOPT | Durable node state, work queue, content hashes, survey cache |
| [worker-pool](./worker-pool/SYSTEM.md) | ADOPT | Isolated agent execution of one node's loop turn |
| [context-packer](./context-packer/SYSTEM.md) | BUILD | Assemble the minimal packet a node needs; enforce the budget |

Two are procured and terminate immediately; only the packer is custom, because only the
packer encodes RSS's own §-structure. That ratio is the point.

**Distinct failure modes** (depth guard 3): store corrupt → resume impossible; worker
fails → node never specified; packer wrong → bad spec or blown budget. Independent.

## 3. Interface Contracts

| | |
|--|--|
| **Inputs** | Tree root path; a goal (cold start) or a changed-node set (warm); budget config (`max_tokens_per_node`, `concurrency`, `survey_ttl_days`, `max_depth`) |
| **Outputs** | Node executions in dependency order; per-run cost ledger (tokens, calls, cache hits); derived index `tree.json`; exit report — node count, depth, **BUILD ratio**, total tokens |

## 4. Invariants (EARS + Epistemic Stage)

- **[Ubiquitous]** The Runner SHALL bound a node's packet to its parent's §1 and §3 plus
  its siblings' §3 — never ancestors above the parent, never uncle subtrees.
  - `EvidenceStage:` Unknown · design intent; becomes Measured under OW-44
- **[Conditional]** IF a packed context exceeds `max_tokens_per_node` THEN THE SYSTEM
  SHALL fail that node with a budget-overflow signal and SHALL NOT truncate the packet.
  - `EvidenceStage:` Unknown — same contract as `harness/baseline.py`: refuse rather than
    guess. A truncated packet manufactures a confident spec from missing information.
- **[Event-driven]** WHEN a node's contract hash is unchanged since the last run THE
  SYSTEM SHALL skip it and every ancestor whose children's hashes are all unchanged.
  - `EvidenceStage:` Unknown · OW-41
- **[Conditional]** IF a validation is expressible as a schema assertion THEN THE SYSTEM
  SHALL evaluate it in code and SHALL NOT spend a model call on it.
  - `EvidenceStage:` Observed (process rule) — §8 field completeness, EARS keyword
    presence, two-child minimum, and depth caps are all schema checks
- **[Conditional]** IF a cached capability survey is older than `survey_ttl_days` THEN THE
  SYSTEM SHALL re-run the survey and SHALL NOT reuse it in a §8 block.
  - `EvidenceStage:` Observed — the recency rule (decomposition-loop §2). A cache with no
    TTL is a mechanism for laundering stale pricing into a resolution
- **[Ubiquitous]** The Runner SHALL treat `tree.json` as a derived cache regenerable from
  the markdown tree; on disagreement the markdown SHALL win.
  - `EvidenceStage:` Observed — preserves hard rule 1 (one incomplete-work surface)
- **[State-driven]** WHILE workers execute concurrently THE SYSTEM SHALL serialize all
  tree writes through a job-store transaction.
  - `EvidenceStage:` Unknown · OW-40

## 5. Architectural Decisions (ADRs)

- **ADR-001: A build system, not a crawler.** The naive runner re-walks the whole tree on
  every invocation. This one is content-addressed and incremental: a node is re-processed
  only when its own inputs changed. Prose edits to §5 do not invalidate anything, because
  the hash covers the **contract surface** (§1 responsibility, §3 interfaces, §8 class and
  selection) — not the file.
- **ADR-002: Bounded neighbour context; overflow fails loudly.** Per-node context is O(1)
  in tree size, not O(depth × breadth). A node that cannot fit its own neighbourhood in
  budget is a bloat signal to be split — not a packet to be trimmed.
- **ADR-003: Derived index, markdown stays sovereign.** `tree.json` lets the scheduler
  plan without opening a single `SYSTEM.md`. It is gitignored and regenerable; it is a
  cache, never a second source of truth, and never a second checklist.
- **ADR-004: Schema-first validation, model second.** Most of what a "validator agent"
  would check is mechanical. Sending a model to confirm §8 has ten fields costs tokens to
  do worse what `jsonschema` does for free. Models are reserved for RESOLVE, where the
  judgment actually lives.
- **ADR-005: Batch the split, fan out the resolve.** Decomposing a node and framing all
  *K* children happens in **one** call — they share the parent's context anyway. RESEARCH
  and RESOLVE then fan out to *K* isolated workers, because each needs its own survey.
  Framing children in *K* separate calls pays the parent packet *K* times for nothing.
- **ADR-006: Parallelism buys latency, not tokens.** Worker fan-out is a wall-clock
  optimization and mildly *increases* token spend (each cold worker re-reads its packet).
  Recorded explicitly so the swarm is never mistaken for the cost lever.
- **ADR-007: Workers get a contract card, not the skill essay.** `recursive-spec/SKILL.md`
  is ~200 lines written for an architect. A worker needs the phase checklist and the §8
  field list. Shipping the full essay to every node is the largest avoidable repeated cost
  in the system, and the card is a stable prefix that caches well across workers.
- **ADR-008: Procurement pruning is the primary cost control, and it already exists.** The
  Runner's job is to not undermine it. No optimization here approaches the savings of a
  BUY/ADOPT resolution that deletes a subtree before it is ever generated.

### Where the tokens actually go

Ranked by savings, largest first. Only the last two are new machinery:

| Lever | Mechanism | Owner |
|-------|-----------|-------|
| Procurement pruning | BUY/ADOPT terminates a subtree unwritten | Technology Resolver (existing) |
| Research memoization | One survey per capability, TTL'd, shared across siblings | job-store |
| Bounded packet | Parent §1/§3 + sibling §3 only; O(1) per node | context-packer |
| Incremental re-walk | Contract-surface hashing; skip unchanged | job-store |
| Schema-first checks | Structural rules cost zero tokens | context-packer / Spec Engine |
| Contract card | Stable cached prefix replaces the skill essay | context-packer |

## 6. Non-leaf note

Not an atomic leaf. Implementation proceeds via the three children — OW-40 … OW-42.
