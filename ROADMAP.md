# Recurspec roadmap

This is the only incomplete-work registry. Completed implementation history belongs in
release notes and git history, not in parallel checklists.

Statuses: `ready`, `blocked`, `research`, `deferred`, `done`.

## Alpha foundation

| ID | Outcome | Status | Evidence |
|---|---|---|---|
| R-001 | Installable `recurspec` package and CLI | done | Build and CLI tests |
| R-002 | One self-contained `recurspec` agent skill | done | Installer drift test |
| R-003 | Tiered Evaluation Gate with explicit baseline promotion | done | Behavioral test suite |
| R-004 | Bounded retries and Negative Pattern memory | done | Behavioral test suite |
| R-005 | Canonical public vocabulary and repository layout | done | Link and legacy-name audits |
| R-006 | Progressive adoption modes and project-fit guidance | done | [Adoption guide](./docs/adoption.md) |

## 1.0: machine-checkable contracts

| ID | Outcome | Status | Blocked by | Contract |
|---|---|---|---|---|
| R-100 | Define a versioned schema for `SYSTEM.md` Contract Nodes | done | — | [Contract Engine](./docs/architecture/contract-engine/SYSTEM.md) |
| R-101 | Validate EARS invariants, Evidence Stages, and terminal §6–§8 sections | done | R-100 | [Contract Engine](./docs/architecture/contract-engine/SYSTEM.md) |
| R-102 | Validate parent/child interface satisfaction | done | R-100 | [Contract Engine](./docs/architecture/contract-engine/SYSTEM.md) |
| R-103 | Detect stale dependency pins and incomplete technology resolutions | done | R-100 | [Stack Resolver](./docs/architecture/stack-resolver/SYSTEM.md) |
| R-104 | Generate a byte-stable, bounded worker contract card | done | R-100 | [Context Packer](./docs/architecture/spec-runner/context-packer/SYSTEM.md) |
| R-105 | Declare explicit machine-checkable ports for the Spec Runner subtree's already-narrated job-store → context-packer → worker-pool data flow, fed from three real root-level ports (`contract_path`, `max_tokens_per_node`, `concurrency`). The remaining root L1 modules (Stack Resolver, Contract Reconciler, Frontier Adapter, Structure Gate, Evaluation Gate) are independently-invoked CLI gates, not a single-invocation pipeline — investigated and found to have no real cross-sibling data flow to port, so they stay prose-only Interface Contracts by design, not by omission | done | R-102 | [Spec Runner](./docs/architecture/spec-runner/SYSTEM.md) |
| R-106 | Parse combined EARS patterns (e.g. state + event in one invariant) as a single invariant, per the design inference already recorded in [foundations.md §1](./docs/research/foundations.md#1-constrained-natural-language-requirements-ears) | done | R-101 | [Contract Engine](./docs/architecture/contract-engine/SYSTEM.md) |

## 2.0: isolated execution

| ID | Outcome | Status | Blocked by | Contract |
|---|---|---|---|---|
| R-200 | Create, evaluate, merge, and dispose Candidate worktrees | done | — | [Evaluation Gate](./docs/architecture/evaluation-gate/SYSTEM.md) |
| R-201 | Enforce maker/checker identity separation in state, not prompts alone | done | — | [Worker Pool](./docs/architecture/spec-runner/worker-pool/SYSTEM.md) |
| R-202 | Persist atomic claims and re-derive state from Markdown | done | R-100 | [Job Store](./docs/architecture/spec-runner/job-store/SYSTEM.md) |
| R-203 | Add CI that runs checks and evaluates changed measurable modules | deferred | R-200 | [Evaluation Gate](./docs/architecture/evaluation-gate/SYSTEM.md) |
| R-204 | Ship a concrete, primary-source-verified agent-runtime adapter behind the Worker Pool seam | research | — | [Worker Pool](./docs/architecture/spec-runner/worker-pool/SYSTEM.md) |

## 3.0: closed-loop reconciliation

| ID | Outcome | Status | Blocked by | Contract |
|---|---|---|---|---|
| R-300 | Detect uncontracted public symbols and structural drift | done | R-101 | [Structure Gate](./docs/architecture/structure-gate/SYSTEM.md) |
| R-301 | Turn Structural Feedback into draft contract changes while deferring Empirical Feedback to the Evaluation Gate | done | R-300 | [Contract Reconciler](./docs/architecture/contract-reconciler/SYSTEM.md) |
| R-302 | Detect adapters that outgrow their procurement seams | done | R-300 | [Stack Resolver](./docs/architecture/stack-resolver/SYSTEM.md) |
| R-303 | Publish Research Frontiers to local and remote trackers | deferred | R-301 | [Frontier Adapter](./docs/architecture/frontier-adapter/SYSTEM.md) |

## Review remediation (2026-08-13)

Fixes for [docs/REVIEW.md](./docs/REVIEW.md), a security/correctness review of the
Evaluation Gate, Worker Pool, and Contract Engine. See that document for the original
reproductions; this table is the sole status record, per hard rule 1.

| ID | Outcome | Status | Evidence |
|---|---|---|---|
| R-600 | Pin evaluation probes to the trusted baseline so a Candidate cannot weaken its own `checks.sh`/`measure.sh` and merge itself | done | `test_isolated_candidate_evaluates_against_trusted_probes_not_the_candidates_own` and related tests in `tests/test_evaluation.py` |
| R-601 | Require a typed CHECK approval, forbid CHECK before any producer, invalidate a stale review on re-produce, and revalidate maker != checker at authorization time | done | `tests/test_worker_pool.py` (check/approval tests), `tests/test_evaluation.py::test_worker_pool_cannot_issue_merge_authorization_to_the_maker` |
| R-602 | Fail closed on non-finite telemetry values, missing metric names, bad direction/tier, and evidence-log corruption that isn't a recoverable final-line truncation | done | `tests/test_evaluation.py` (NaN/contradiction/`EvidenceInstrumentError` tests) |
| R-603 | Reject hollow non-leaf nodes and disconnected/multi-parent Contract Trees | done | `tests/test_contract.py` (hollow node, unreachable node, multiple-parents, disconnected-cycle tests) |
| R-604 | Exclude Recurspec's own runtime state from the baseline cleanliness check so the documented `--worker-state` path cannot block evaluation | done | `test_isolated_candidate_ignores_recurspec_runtime_state_when_checking_cleanliness` in `tests/test_evaluation.py`; `.gitignore` |
| R-605 | Align the bundled skill's references with the shipped CLI and canonical vocabulary | done | `tests/test_skill_references.py` |
| R-606 | Add the missing `job-store`/`worker-pool` probe scripts and fix the Contract Engine's multi-object `measure.sh` payload | done | `tests/test_modules.py` |
| R-607 | Reject floating dependency versions in both the inventory and §8 Pin fields | done | `tests/test_technology_resolver.py` (floating-version tests) |
| R-608 | Validate the CLI `module` argument as a single safe path segment and reject a structure/stack root that escapes the repository | done | `tests/test_evaluation.py` (unsafe module name tests), `tests/test_structure_gate.py::test_structure_gate_refuses_a_source_root_that_escapes_the_repository` |

## Follow-up hardening (2026-08-13)

A second, deeper adversarial pass over the R-600–R-608 fixes above found narrower gaps
in the same seams. `contract.py`'s sole-root check was also examined for whether it
should require the root to be level 0 (L0); doing so broke
`test_validate_contract_accepts_an_independently_authored_two_stage_tree`, which is
deliberate support for validating a composable subtree that is not itself an L0 root
(the same "investigated, by design" precedent as R-105) — no change was made there.

| ID | Outcome | Status | Evidence |
|---|---|---|---|
| R-609 | Pin the whole `tests/` tree (not just `checks.sh`/`measure.sh`) to the trusted baseline, since every bundled `checks.sh` shells out to test files a Candidate could otherwise weaken | done | `test_isolated_candidate_evaluates_against_trusted_tests_dependency_not_the_candidates_own` in `tests/test_evaluation.py` |
| R-610 | Bind a CHECK's approval to the maker generation it reviewed so a produce racing an in-flight CHECK call cannot authorize content the checker never saw | done | `test_a_concurrent_re_produce_invalidates_an_in_flight_check` in `tests/test_worker_pool.py` |
| R-611 | Only forgive a non-newline-terminated final evidence line as a torn write; a complete-but-corrupt final line or a non-object JSON scalar now raises instead of being skipped or crashing later with `AttributeError` | done | `test_read_events_raises_on_a_complete_but_corrupt_final_line`, `test_read_events_raises_on_a_non_object_json_scalar` in `tests/test_evaluation.py` |
| R-612 | Resolve `python3`/`python` at runtime in every bundled `checks.sh`/`measure.sh` instead of assuming a bare `python` alias is on PATH | done | `test_bundled_probes_never_invoke_a_bare_python_command` in `tests/test_modules.py` |
| R-613 | Stop excluding the whole `.recurspec/` directory from the baseline cleanliness check; only Recurspec's own untracked generated runtime-state paths are ignorable, so a tracked dirty file anywhere (including under `.recurspec/`) still blocks evaluation | done | `test_isolated_candidate_still_refuses_a_tracked_dirty_file_under_recurspec` in `tests/test_evaluation.py` |
| R-614 | Accept ecosystem-valid immutable versions (`v`-prefixed tags, hex revisions, `algo:hex` digests) as exact, and reject malformed pins (leading/trailing/doubled separators), instead of only recognizing digit-led dotted strings | done | `test_dependency_inventory_accepts_ecosystem_valid_exact_forms`, expanded `test_dependency_inventory_rejects_a_floating_version` in `tests/test_technology_resolver.py` |
| R-615 | Reject a Contract Node §6 declaration whose implementation/test path is absolute, drive-lettered, or escapes the repository via `..`, instead of joining it onto the repository root unchecked | done | `test_structure_gate_rejects_a_declared_path_that_escapes_the_repository`, `test_structure_gate_rejects_an_absolute_declared_path` in `tests/test_structure_gate.py` |
| R-616 | Remove the bundled skill's one repository-only relative link (into `docs/research/`, which is not packaged) and add a standing check that no skill reference links outside the installed skill directory | done | `test_skill_references_never_link_outside_the_installed_skill` in `tests/test_skill_references.py` |

## Optimization and bug pass (2026-08-14)

A general (non-adversarial) pass over the remaining source not covered by the reviews
above, looking for correctness and performance defects rather than security bypasses.

| ID | Outcome | Status | Evidence |
|---|---|---|---|
| R-617 | Resolve `tree_root` before walking it in `build_tree_index()`; a relative `tree_root` compared unresolved `rglob()` paths against `resolve_child_path()`'s always-resolved output, so every non-root node's `parent_id` silently came back `None` instead of raising or resolving correctly | done | `test_build_tree_index_resolves_parent_ids_from_a_relative_tree_root` in `tests/test_contract.py` |
| R-618 | Make Worker Pool authorization persistence single-writer: `_persist_authorizations()` now always includes candidate identity from in-memory state, so `merge_authorization()` no longer does its own unsynchronized, non-atomic read-modify-write of the same file `dispatch()` writes atomically under lock - which could race a concurrent `dispatch()` call and, even sequentially, went stale the moment the next `dispatch()` rewrote the file from its own snapshot | done | `test_persisted_candidate_identity_survives_a_later_unrelated_dispatch` in `tests/test_worker_pool.py` |
| R-619 | Make `JobStore.rebuild_from_tree()` commit as one transaction instead of one per node, so a tree rebuild is atomic (a crash mid-rebuild can no longer leave a mix of old and new state) and does not scale connection/lock overhead with tree size | done | `test_rebuild_from_tree_commits_as_a_single_transaction` in `tests/test_job_store.py` |
| R-620 | Add an index on `nodes.status` so `claim_next_ready()`'s `WHERE status = 'ready'` is no longer a full table scan under concurrent workers | done | `test_nodes_table_is_indexed_by_status_for_claim_next_ready` in `tests/test_job_store.py` |

## Research and validation

These items are required before claiming that Recurspec improves engineering outcomes.
The cited foundations motivate individual mechanisms; they do not validate Recurspec as a
whole.

| ID | Study | Status | Acceptance criterion |
|---|---|---|---|
| R-400 | Two real-project case studies | research | Reproducible before/after repositories and decision logs |
| R-401 | Procurement-seam effectiveness | research | Measure avoided custom code and later replacement cost |
| R-402 | Negative Pattern effectiveness | research | Compare repeated-failure rate with and without repair memory |
| R-403 | Contract drift effectiveness | research | Compare detected and escaped code/contract mismatches |
| R-404 | Domain-general example outside web software | ready | Published CLI, systems, or data-pipeline Contract Tree |
| R-405 | Pre-register evaluation metrics and analysis | done | [Evaluation protocol](./docs/research/evaluation-protocol.md), published before any R-400–R-403 outcome data is collected |

## Long horizon: compounding intelligence

| ID | Outcome | Status | Constraint |
|---|---|---|---|
| R-500 | Export a privacy-preserving decision corpus | research | Explicit opt-in; no source, prompts, secrets, or proprietary metrics |
| R-501 | Learn reusable failure predictors from Negative Patterns | blocked | R-400, R-402, R-500 |
| R-502 | Recommend Decision Classes from comparable outcomes | blocked | R-401, R-500; recommendations remain reviewable evidence, never authority |

## Intentionally out of scope

- A web interface before the CLI and contract schema stabilize.
- Model-judge scores as autonomous merge authority.
- Claims of formal proof from tests, measurements, or model consensus.
- Centralized telemetry without explicit project-level opt-in.
