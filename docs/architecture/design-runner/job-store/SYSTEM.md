# Job Store (L2)

## 1. System Intent & Responsibility

Hold the Runner's durable state: node status, contract hashes, the ready queue, and the
TTL'd capability-survey cache — transactionally, under concurrent workers.

**Does not own:** the spec content itself (that is markdown in git, and this store is a
derived cache of it), packet assembly (context-packer), or worker lifecycle (worker-pool).

## 2. Sub-System Decomposition

**Atomic leaf (procured).** Resolved ADOPT uniformly — the seam is specified below; the
engine's internals are not ours to decompose.

## 3. Interface Contracts

| | |
|--|--|
| **Inputs** | Node upserts `{node_id, parent_id, class, status, contract_hash}`; survey writes `{capability_key, result, sources, fetched_at}`; claim/release requests |
| **Outputs** | Next ready node (atomic claim); dirty set for a given change; survey hit or `stale`/`miss`; the derived `tree.json` projection |

**Contract hash** covers §1 responsibility, §3 interfaces, and §8 class + selection — the
node's *contract surface*. Editing §5 prose does not dirty anything downstream.

## 4. Invariants (EARS + Epistemic Stage)

- **[Ubiquitous]** The Store SHALL be reconstructible in full from the markdown tree plus
  git history; losing it SHALL cost time, never information.
  - `EvidenceStage:` Asserted · OW-40
- **[State-driven]** WHILE multiple workers are active THE SYSTEM SHALL hand a given node
  to at most one worker (atomic claim).
  - `EvidenceStage:` Asserted
- **[Event-driven]** WHEN a node's contract hash changes THE SYSTEM SHALL mark that node
  and its parent dirty, and SHALL NOT mark its siblings dirty.
  - `EvidenceStage:` Asserted — sibling isolation is what makes re-walks cheap; a sibling
    only dirties if it names the changed node in its own §3
- **[Conditional]** IF a survey row's `fetched_at` is older than `survey_ttl_days` THEN
  THE SYSTEM SHALL report `stale` and SHALL NOT return it as a hit.
  - `EvidenceStage:` Asserted (recency rule)
- **[Conditional]** IF the store disagrees with the markdown tree THEN THE SYSTEM SHALL
  discard the store's row and re-derive it.
  - `EvidenceStage:` Asserted — markdown is sovereign

## 5. Architectural Decisions (ADRs)

- **ADR-001:** Runtime node status lives here, not in `ROADMAP.md` and not in `SYSTEM.md`
  frontmatter. It is ephemeral run state in a regenerable cache, so hard rule 1 (one
  incomplete-work surface) is preserved — this is not a second checklist, and nothing a
  human is expected to read lives in it.
- **ADR-002:** Hash the contract surface, not the file. File-level hashing invalidates a
  whole subtree because someone fixed a typo in an ADR.
- **ADR-003:** The survey cache is keyed by *normalized capability phrase*, not node id —
  siblings asking "is there a managed X" must collide on purpose. That collision is the
  saving.

## 6. Leaf Execution & Test Seam

- **Implementation:** `src/spec_runner/store.py` (seam over the embedded engine)
- **Tests:** `tests/test_job_store.py` — must cover: atomic claim under concurrency;
  sibling non-invalidation; TTL expiry returns `stale` not a hit; full rebuild from
  markdown reproduces the store; markdown wins on disagreement
- **Open work:** OW-40, OW-41

## 7. Measurement Seams

- **Primary metric:** `rewalk_amplification` — nodes re-processed ÷ nodes actually changed
  (direction `lower`, floor 1.0). A naive crawler scores *tree size*; correct
  incrementality scores near 1
- **Secondary:** `survey_cache_hit_rate` (direction `higher`); `claim_conflict_rate`
  (direction `lower`)
- **Evaluation Gate:** `modules/job-store/measure.sh`
- **Backpressure:** `modules/job-store/checks.sh`
- **Telemetry:** per-run `{nodes_total, nodes_dirty, nodes_processed, cache_hits, cache_stale}`
- **Branching:** worktree candidate; keep only on checks pass ∧ no `rewalk_amplification`
  regression

## 8. Technology Resolution

- **Decision class:** ADOPT
- **Selected:** SQLite via the Python standard library's `sqlite3` module, with content
  hashing delegated to git's object hashing. Both are already dependencies of this repo
  (the evaluation gate is Python; the tree is versioned in git).
  - **Pin:** not recorded — `sqlite3` ships with the interpreter, so the pin is the Python
    version declared at implementation. Verify against live docs before writing §8's final
    form (OW-40); this spec does not assert a version it has not checked.
- **Standard / protocol:** SQL; git object format
- **Alternatives considered:**
  | Option | Why not |
  |--------|---------|
  | Neo4j / a graph database | The tree is a filesystem hierarchy whose source of truth is markdown in git. A graph DB adds a server and a second authoritative store — a direct hard-rule-1 conflict — to model a parent pointer |
  | Redis + Celery | Requires a running broker for what is a single-machine, single-user CLI walk |
  | PostgreSQL | Ops burden and a network hop for a store that must be disposable by design (ADR-001) |
  | Temporal / Prefect / Dagster | Genuine fit for durable execution, and the closest rejection. Rejected on weight: they own scheduling and retry semantics we would then have to bend around the resolve-before-decompose rule, for a workload measured in hundreds of nodes on one machine. Revisit if the Runner ever spans machines |
  | Plain JSON file | No transactions. Concurrent workers race on it, and the atomic-claim invariant cannot be met |
- **Fit gap:** SQLite gives durability and transactions but no queue semantics, no TTL, and
  no dirty-propagation — those are the thin layer `store.py` adds. **This gap is why the
  parent node has a BUILD child at all**, and it is deliberately kept this small.
- **Seam:** `src/spec_runner/store.py` — no SQL escapes this module
- **Exit cost:** LOW — the schema is five tables and the store is regenerable from
  markdown, so a migration is a rebuild, not a data export
- **Cost model:** zero licence, zero hosting; disk only
- **Liability transferred:** none (embedded, local, no PII)
- **Operational owner:** us
- **Failure mode:** a corrupt store halts the run. Recovery is `rm` plus a full re-derive
  from markdown — which is exactly why invariant 1 forbids it holding unique information.
- **Open questions:** OW-40 (pin + schema), OW-41 (dirty-propagation rules)
