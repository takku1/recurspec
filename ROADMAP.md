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
| R-203 | Add CI that runs checks and evaluates changed measurable modules | done | R-200 | [Evaluation Gate](./docs/architecture/evaluation-gate/SYSTEM.md) |
| R-204 | Ship a concrete, primary-source-verified agent-runtime adapter behind the Worker Pool seam. Evidence: [survey](./docs/research/r-204-runtime-survey.md), `src/recurspec/spec_runner/runtime.py`, `tests/test_runtime.py` | done | — | [Worker Pool](./docs/architecture/spec-runner/worker-pool/SYSTEM.md) |

## 3.0: closed-loop reconciliation

| ID | Outcome | Status | Blocked by | Contract |
|---|---|---|---|---|
| R-300 | Detect uncontracted public symbols and structural drift | done | R-101 | [Structure Gate](./docs/architecture/structure-gate/SYSTEM.md) |
| R-301 | Turn Structural Feedback into draft contract changes while deferring Empirical Feedback to the Evaluation Gate | done | R-300 | [Contract Reconciler](./docs/architecture/contract-reconciler/SYSTEM.md) |
| R-302 | Detect adapters that outgrow their procurement seams | done | R-300 | [Stack Resolver](./docs/architecture/stack-resolver/SYSTEM.md) |
| R-303 | Publish Research Frontiers to local and remote trackers | done | R-301 | [Frontier Adapter](./docs/architecture/frontier-adapter/SYSTEM.md) |

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
| R-619 | Make `JobStore.rebuild_from_tree()` commit as one transaction instead of one per node, so a tree rebuild is atomic (a crash mid-rebuild can no longer leave a mix of old and new state) and does not scale connection/lock overhead with tree size | done | `test_rebuild_from_tree_commits_as_a_single_transaction` and `test_rebuild_from_tree_rolls_back_when_a_node_upsert_fails` in `tests/test_job_store.py` |
| R-620 | Add an index on `nodes.status` so `claim_next_ready()`'s `WHERE status = 'ready'` is no longer a full table scan under concurrent workers | done | `test_nodes_table_is_indexed_by_status_for_claim_next_ready` in `tests/test_job_store.py` (`PRAGMA index_info` asserts the index is on `nodes.status`) |

## REVIEW3 remediations (2026-08-14)

Findings from `REVIEW3-tobedeleted when done.md`. That note reused R-617–R-622, which
already named the optimization pass above, so these tickets continue from R-621.

| ID | Outcome | Status | Evidence |
|---|---|---|---|
| R-621 | Pin the whole `modules/` tree and root pytest/ruff config into the Candidate worktree so a helper outside `tests/` cannot weaken the judge | done | `test_isolated_candidate_evaluates_against_trusted_module_helpers_not_the_candidates_own` |
| R-622 | Reject malformed pins such as `1latest` that the previous exact-version heuristic accepted | done | expanded `test_dependency_inventory_rejects_a_floating_version` |
| R-623 | Resolve declared §6 paths and reject repository-relative symlinks whose target leaves the tree | done | `test_structure_gate_rejects_a_symlink_whose_target_escapes_the_repository` |
| R-624 | Validate every decoded evidence object against the required event schema; `{}` fails closed | done | `test_read_events_raises_on_an_empty_object` |
| R-625 | Pass `sys.executable` to probes as `RECURSPEC_PYTHON` and invoke Ruff as `python -m ruff` | done | `test_run_script_exports_the_running_interpreter`; bundled `modules/*/*.sh` |
| R-626 | Put the complete EARS bibliographic citation in the installed skill instead of pointing at a repository-only file | done | `test_skill_design_reference_carries_a_self_contained_ears_citation` |

## Live-use follow-up (2026-08-15)

Off-repo Grok sessions loaded the skill and skipped the CLI. They treated any existing
`SYSTEM.md` as a finished Contract Tree and kept process debt in rival registries.

| ID | Outcome | Status | Evidence |
|---|---|---|---|
| R-627 | Classify project readiness with `recurspec status` and require that classification before design: `missing`, `not_recurspec`, `invalid`, or `valid`. Rival registries do not replace `ROADMAP.md` | done | `tests/test_project_status.py`; skill first-action tests in `tests/test_skill_references.py` |
| R-628 | Report declared §7 probe scripts that are not on disk. Contract Engine still validates Markdown only (no repository root). Structure Gate owns path existence; `status` surfaces the same list so the first action cannot say `ready` over a fictional `measure.sh` | done | `test_declared_probe_paths_resolves_a_bare_checks_sibling`; `test_status_repairs_when_a_declared_probe_is_missing` |
| R-629 | Discover the extra well-known Contract Tree at `.recurspec/contracts` and classify it separately from `docs/architecture`. Do not merge the two trees; composition stays per root | done | `test_status_classifies_an_extra_contracts_tree` |
| R-630 | First action still runs when the user asked for a paper, skill install, or research. Status the *subject* repository. A `missing` tree on a prose-only folder is expected; do not invent a Contract Tree for a preprint | done | `test_skill_requires_status_on_paper_and_research_asks` |
| R-631 | A work list is not one Contract Node. `recurspec fanout` splits it into one strategy handoff per item; the skill forbids implementing 1–N in a single shared context | done | `tests/test_fanout.py`; skill work-list tests |
| R-632 | Skill close-out states what each evidence class licenses. Tests are not outcome evidence; "no data yet" is a complete finding | done | `test_skill_states_evidence_class_licensing` |

## REVIEW4 remediations (2026-08-15)

Findings from an internal follow-up snapshot (`REVIEW4`, not committed — its findings
are captured here per hard rule 1, then the note is deleted) that checked whether the
R-600–R-639 fixes above still had gaps. Continues from R-640.

| ID | Outcome | Status | Evidence |
|---|---|---|---|
| R-640 | Add an optional, baseline-only trusted-input manifest (`.recurspec/trusted-inputs.json`) so a project can pin probe-adjacent inputs the fixed lists cannot anticipate (a `scripts/` helper, a plugin config); also add `setup.cfg`, `tox.ini`, `sitecustomize.py`, `usercustomize.py`, and a `scripts/` tree to the fixed trusted set. A malformed manifest or an entry that escapes the repository fails closed rather than silently trusting less than declared | done | `test_isolated_candidate_evaluates_against_a_manifest_declared_trusted_helper`, `test_load_trusted_manifest_fails_closed_on_malformed_content`, `test_load_trusted_manifest_refuses_a_path_that_escapes_the_repository` in `tests/test_evaluation.py` |
| R-641 | Validate every decoded evidence event's `event_type` against the known set this codebase actually writes, reject an unparseable `ts`, and require the event's own `module` field to agree with the log it was read from — closing the gap where a complete, well-typed but semantically bogus event (invented `event_type`, wrong `module`, garbage timestamp) previously passed the common-envelope check | done | `test_read_events_raises_on_a_module_that_disagrees_with_its_own_log`, `test_read_events_raises_on_an_unrecognized_event_type`, `test_read_events_raises_on_an_unparseable_timestamp` in `tests/test_evaluation.py` |
| R-642 | Tighten `_looks_exact`'s semver pattern so a non-numeric core component (e.g. `1.foo`) cannot pass as an exact version; only `-prerelease`/`+build` suffixes may contain non-numeric text, matching where semver actually allows one | done | expanded `test_dependency_inventory_rejects_a_floating_version` in `tests/test_technology_resolver.py` |
| R-643 | Add an optional §8 `Reference kind` field (`version` \| `tag` \| `commit` \| `digest`); when declared, validate the Pin against only that grammar instead of the blended "any of the three" check. Absent a declaration, behavior is unchanged. Deliberately does not attempt to verify that a declared `tag` is actually immutable (Recurspec cannot ask the vendor) - that residual ambiguity is recorded (ADR-006), not solved | done | `test_resolution_audit_accepts_a_pin_matching_its_declared_reference_kind`, `test_resolution_audit_rejects_a_pin_that_does_not_match_its_declared_reference_kind`, `test_resolution_audit_rejects_an_unrecognized_reference_kind` in `tests/test_technology_resolver.py` |
| R-646 | Validate `merge_authorization` evidence events against their one fixed producer shape (`{"maker_id": str, "checker_id": str}`, both non-empty) - the single event type where "event-specific schema validation" (REVIEW4) has unambiguous value, since it is the maker/checker separation audit trail. Investigated extending this to `baseline`/`candidate`/`decision`/`signal_d`/`negative_pattern` and did not: their `metrics` shape is legitimately variable by design (e.g. an early-failure `decision` logs `metrics={}`), downstream consumers already guard with `.get()`/`_numeric()`, and mandating a stricter shape would reject data the system itself intentionally tolerates | done | `test_read_events_raises_on_a_merge_authorization_event_missing_identities`, `test_read_events_accepts_a_well_formed_merge_authorization_event` in `tests/test_evaluation.py` |
| R-644 | Enable `flake8-bandit` (`S`) and `flake8-bugbear` (`B`) in the Ruff lint config and fix or justify every finding: resolve `git`/`gh` to absolute paths instead of bare PATH lookups, document the two intentional `shell=True`/subprocess uses inline, and fix the incidental `B007`/`C420` hits the same sweep turned up | done | `pyproject.toml` `[tool.ruff.lint]`; `ruff check src tests` passes with zero suppressions outside `tests/*` (asserts and test-fixture `git` spawns) |
| R-645 | Raise `[build-system] requires` from `setuptools>=77` to `setuptools>=83` (CVE-2026-59890 / PYSEC-2026-3447, fixed 83.0.0): the old floor permitted a known-vulnerable version, which a dependency-graph scanner flags from `pyproject.toml` alone, without installing anything. `pip-audit` against a clean install of `recurspec[runtime,rust]` found no vulnerability in any package Recurspec itself declares (`jsonschema`, `anthropic`, `tree-sitter`, `tree-sitter-rust`); the only finding was this transitive `setuptools`. Note: a bare `python -m venv` seeds a vulnerable `setuptools` from the *interpreter's own* bundled `ensurepip` before any project is installed — this floor cannot fix that copy; the runtime fix is upgrading the local Python/pip, not a Recurspec dependency change | done | `pyproject.toml` `[build-system]`; `python -m build` still succeeds |

## Research and validation

These items are required before claiming that Recurspec improves engineering outcomes.
The cited foundations motivate individual mechanisms; they do not validate Recurspec as a
whole.

| ID | Study | Status | Acceptance criterion |
|---|---|---|---|
| R-400 | Two real-project case studies | research | Reproducible before/after repositories and decision logs. Log template: [case-study-log.md](./docs/research/case-study-log.md). No outcome data yet. |
| R-401 | Procurement-seam effectiveness | research | Measure avoided custom code and later replacement cost. Same log template. No outcome data yet. |
| R-402 | Negative Pattern effectiveness | research | Compare repeated-failure rate with and without repair memory. Same log template. No outcome data yet. |
| R-403 | Contract drift effectiveness | research | Compare detected and escaped code/contract mismatches. Same log template. No outcome data yet. |
| R-404 | Domain-general example outside web software | done | [docs/examples/log-archive](./docs/examples/log-archive/SYSTEM.md); `test_log_archive_example_tree_is_a_valid_contract_tree` |
| R-405 | Pre-register evaluation metrics and analysis | done | [Evaluation protocol](./docs/research/evaluation-protocol.md), published before any R-400–R-403 outcome data is collected |
| R-406 | CLI that writes a pair log and records assignment before either arm starts. Refuses Recurspec as a subject and refuses a second coin flip | done | `tests/test_study.py`; pair logs under [docs/research/pairs](./docs/research/pairs) |
| R-633 | Refuse `study init` when either task id already has Recurspec fingerprints in the subject project | done | `test_study_init_refuses_a_contaminated_subject`; `check_contamination` |
| R-634 | `study accept` records an independent accept only after a mechanically executed verify command exits 0, and refuses when maker equals checker | done | `test_accept_arm_records_a_passing_verify_command`; `test_accept_arm_refuses_a_failing_verify_and_leaves_the_log`; `test_accept_arm_refuses_same_identity_before_running_verify` |
| R-635 | Structure Gate language-adapter abstraction (behavior-preserving refactor of the Python AST walker) | done | `LanguageAdapter` + default `PYTHON_ADAPTER`; `test_check_structure_uses_an_injected_language_adapter` |
| R-636 | Optional Rust Structure Gate adapter (`recurspec[rust]`, tree-sitter) | done | `test_rust_adapter_detects_pub_items_and_skips_cfg_test`; `test_available_adapters_omits_rust_when_the_extra_is_missing` |
| R-637 | Evidence-stage honesty report: count stages and list Sampled/Measured/Proved invariants that name no check. Observation only — never fail the tree. Formality-evasion: Bowen & Hinchey; Shipman & Marshall | done | `test_evidence_audit_lists_unlicensed_sampled_and_counts_unknown`; `recurspec contract evidence` |
| R-638 | Optional Best Known State metric-only implementor packet (hide prior candidate code). Design-fixation ablation, not a default | done | `test_implementor_bks_metrics_only_omits_source_even_when_files_are_named`; `evaluate --bks-metrics-only`. Ablation outcome data is still absent. |
| R-639 | Clarify that `ESCALATE` is the path when the Contract Node (the search space) may be wrong, not only when the candidate is wrong. Do not add a fourth gate outcome | done | evaluation-gate ADR-006; `test_skill_states_escalate_is_the_wrong_space_path` |

## Long horizon: compounding intelligence

| ID | Outcome | Status | Constraint |
|---|---|---|---|
| R-500 | Export a privacy-preserving decision corpus | done | Explicit opt-in (`recurspec corpus export --i-opt-in`); redacts reason, branch, metric values, source, and prompts. `tests/test_corpus.py` |
| R-501 | Learn reusable failure predictors from Negative Patterns | blocked | R-400, R-402, R-500. Instrument: `recurspec predict` reports reason frequencies or refuses; no trained model. |
| R-502 | Recommend Decision Classes from comparable outcomes | blocked | R-401, R-500; recommendations remain reviewable evidence, never authority. Instrument: `recurspec recommend` refuses because the R-500 corpus redacts Decision Class. |

## Intentionally out of scope

- A web interface before the CLI and contract schema stabilize.
- Model-judge scores as autonomous merge authority.
- Claims of formal proof from tests, measurements, or model consensus.
- Centralized telemetry without explicit project-level opt-in.
