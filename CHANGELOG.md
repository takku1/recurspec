# Changelog

All notable changes follow [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Changed

- Completed the repository-wide consolidation pass: removed the orphaned review snapshot
  and obsolete identity example, aligned every active architecture contract with shipped
  modules, removed completed-ticket and nonexistent-archive references, and indexed the
  retained research surfaces.
- Probe templates now refuse with exit 2 until real assertions and measurements replace
  them; placeholders can no longer authorize KEEP or emit a fabricated numeric default.
- Repository integrity tests now reject retired workflow vocabulary, unindexed top-level
  documentation, stale ROADMAP references, and blockers that are no longer open.
- Every `Sampled` architecture invariant now names an executable test. The remaining
  `Unknown` findings are intentional claim boundaries, not missing licenses.
- R-701: `stack check` now accepts PEP 440 exact releases (`5.0.0.93`, `2.9.0.post0`,
  `1.2.3rc1`, `1.0.0.dev1`). The semver-shaped test rejected them as floating, and one
  offending package refused the whole `--inventory`, making the gate unusable on ordinary
  Python environments.
- R-701: `structure check` and `reconcile plan` infer the source root from the repository
  layout instead of defaulting to `src/recurspec`, so both gates work outside this
  repository. `--source-root` still overrides, and an ambiguous layout fails closed
  naming the flag.
- R-701 (review): the fence fix covered only the contract parser; `declared_paths` and
  `declared_probe_paths` still harvested fenced §6/§7 examples as real declarations, so
  the Structure Gate could believe a nonexistent file was covered. Both parsers now share
  one stripper.
- R-701 (review): `compare()`'s guard exempted `tolerance_pct == 0`, so `--tolerance 0` -
  the strictest setting - still reported every sub-2% regression as neutral. "Any
  regression blocks" is now spelled tolerance 0 **and** noise 0.
- R-701 (review): an ambiguous layout now fails closed with
  `structure.source_root.ambiguous` naming `--source-root`, instead of silently auditing
  all of `src/`; a missing repository stays a diagnostic rather than an instrument crash.
- R-701 (review): reconciled the Contract Tree with the code - contract-engine,
  structure-gate, evaluation-gate, and stack-resolver each declare the behaviour these
  commits changed, and evaluation-gate §6 lists `metrics.py` as implementation.
- R-701: contract validation ignores fenced code blocks. Sections and invariants inside
  a fence were parsed as declarations, so a node whose sections 4-8 existed only inside a
  fenced example validated clean and its illustrative `Proved` stage entered the tree.
- R-701: CI now runs the gates the project ships - `structure check`, `stack check`,
  `reconcile plan`, and a skill install/verify round-trip - and adds a `windows-latest`
  job. Four of the project's own gates previously ran only when a maintainer remembered,
  which is how a source-root default that broke every other repository survived.
- R-701: `compare()` refuses `noise_pct >= tolerance_pct`. The noise band is tested
  first, so that configuration reported every regression as neutral and silently voided
  the primary gate.
- R-701: split the 560-line `build_parser` into one `_add_*_parser` builder per
  command. Verified by diffing the help text of all 28 parsers before and after, and
  guarded by a test asserting every defined builder is wired in.
- R-701: `check` text output now identifies each finding's subject. The JSON envelope
  always carried `details.path`; the text renderer dropped it, printing every `Unknown`
  evidence finding as the same unactionable line.


- R-700-04: removed the duplicated decision-class table and Technology Resolution block
  from the bundled `design.md`, which had already drifted from `resolve.md` and the
  fields `recurspec stack check` enforces. Both references now document the same twelve
  required fields plus the BUILD-only `Justification`, pinned by a repository test.
- R-700-02: condensed the bundled skill into a small controller around
  `DISCOVER -> RESOLVE -> EXECUTE -> CHECK -> RECONCILE`; detailed design, resolution,
  and reconciliation rules remain lazy-loaded references.
- Added bounded Coverage Review and evidence-driven adaptive planning without adding an
  editable project graph, Scrum ceremonies, or model-judge authority.
- R-700-03: made `ROADMAP.md` incomplete-work-only, replaced obsolete multi-stage process
  prose, and removed integrated consolidation scratch notes while retaining the standard
  `src/recurspec` package layout and independently failing Contract Nodes.

### Removed

- R-701: the `recurspec recommend` command. It ignored `--corpus` and raised
  unconditionally, and could never succeed because the exported corpus redacts Decision
  Class by construction. `ROADMAP.md` R-502 remains the single record of the block, and a
  test now asserts the redaction directly.

### Added

- R-700-01: one immutable `check_project()` report and `recurspec check` command combine
  contract, Evidence Stage, structure, Technology Resolution, and Research Frontier
  checks without changing project state. Typed Findings preserve evidence licenses;
  narrow commands remain compatible.
- R-627: `recurspec status` classifies a repository as `missing`, `not_recurspec`,
  `invalid`, or `valid` before design. The bundled skill must run it first and treats
  unmarked `SYSTEM.md` files as source material, not Recurspec contracts. Rival
  incomplete-work files (`FEATURE_GAPS.md` and similar) do not replace
  `ROADMAP.md`.
- R-628: `status` and `structure check` report §7 `checks.sh`/`measure.sh` paths that
  are not on disk and route `repair` instead of `ready`.
- R-629: `status` classifies an extra Contract Tree at `.recurspec/contracts`.
- R-630: the skill still requires `status` on the subject repository when the user
  asked for a paper, install, or research.
- R-631: `recurspec fanout` splits a work list into one strategy handoff per item.
  The skill treats a numbered list as N nodes, not one shared context.
- R-632: the skill close-out states what each evidence class licenses and forbids
  promoting a passing test suite to an outcome claim.
- R-406: `recurspec study init|assign|list` writes R-400 pair logs, coin-flips
  assignment, refuses Recurspec as a subject, and refuses a second flip.
- R-633: `study init` refuses a subject project that already has Recurspec
  fingerprints (strategy handoff, evidence log, or tracker mention) for either
  task id.
- R-634: `recurspec study accept` records an independent arm accept only after
  a named verify command is executed and exits 0. Maker and checker identities
  must differ; a failing command leaves the pair log untouched.
- R-637: `recurspec contract evidence` reports Evidence Stage counts and
  Sampled/Measured/Proved invariants that name no check. The report never
  fails a valid Contract Tree.
- R-635: Structure Gate extracts public symbols through a `LanguageAdapter`
  seam. The default adapter remains Python `ast`.
- R-636: optional extra `recurspec[rust]` adds a tree-sitter Rust adapter.
  Top-level `pub` items are the public surface; `#[cfg(test)]` modules are
  excluded. A missing extra omits the adapter instead of failing.
- R-639: `ESCALATE` is documented as the path when the Contract Node (the
  search space) may be wrong. No fourth gate outcome.
- R-638: `implementor_bks(..., metrics_only=True)` and `evaluate --bks-metrics-only`
  expose the Best Known State metric vector and omit prior source.
- R-501 instrument: `recurspec predict` reports Negative Pattern frequencies or
  refuses. R-502 stays blocked and, per Removed below, ships no command.
- R-640: an optional `.recurspec/trusted-inputs.json` manifest lets a project pin
  extra probe-adjacent inputs into the Candidate worktree; `setup.cfg`, `tox.ini`,
  `sitecustomize.py`, `usercustomize.py`, and a `scripts/` tree join the fixed
  trusted set. A malformed or path-escaping manifest fails closed.
- R-641: evidence events now must declare a known `event_type`, a parseable `ts`,
  and a `module` that agrees with the log they were read from; a decoded-but-bogus
  event now raises `EvidenceInstrumentError` instead of being trusted.
- R-642: `_looks_exact` rejects a version whose core has a non-numeric dotted
  component (e.g. `1.foo`); only `-prerelease`/`+build` suffixes may be non-numeric.
- R-644: `ruff check` now runs `flake8-bandit` (S) and `flake8-bugbear` (B). `git`
  and `gh` invocations resolve to an absolute path instead of a bare PATH lookup;
  the two intentional `subprocess`/`shell=True` uses carry inline justification.
- R-645: `[build-system] requires` raised to `setuptools>=83` (CVE-2026-59890 /
  PYSEC-2026-3447). `pip-audit` against a clean `recurspec[runtime,rust]` install
  found no vulnerability in anything Recurspec itself declares; a bare `python -m
  venv` seeds a vulnerable `setuptools` from the interpreter's own bundled
  `ensurepip` regardless of this project, which the floor bump cannot fix.
- R-643: optional §8 `Reference kind` field (`version`/`tag`/`commit`/`digest`) on a
  Technology Resolution Pin; when declared, the Stack Resolver validates against only
  that grammar instead of the blended ecosystem-neutral check. Undeclared pins are
  unaffected.
- R-646: `merge_authorization` evidence events are now validated against their one
  fixed producer shape (non-empty `maker_id`/`checker_id`); the other event types'
  `metrics` payload is left envelope-only because their shape is legitimately variable
  by design.
- Implemented the deterministic Structure Gate (ROADMAP R-300) with a standard-library
  Python AST adapter, Contract Node §6 ownership and test-surface checks, bounded
  changed-file scans, stable diagnostics, CLI exit codes, and a seeded false-negative
  measurement seam. The installable package no longer depends on interactive graph
  tooling for this gate.
- Implemented the draft-only Contract Reconciler (ROADMAP R-301). It converts Structure
  Gate diagnostics and line-count bloat into deterministic review actions, emits
  schema-valid `Unknown` leaf drafts without writing them, refuses broken structural
  evidence, and explicitly defers Signal D to the Evaluation Gate.
- Implemented Stack Resolver audits (ROADMAP R-103 and R-302): required §8 field checks,
  exact pin comparison against explicit dependency inventories, indeterminate refusal
  when pin evidence is missing, DEFER vendor guards, and WRAP seam-spread/line-growth
  signals. Dogfooding corrected stale Contract Engine and Worker Pool decision classes.
- Implemented Candidate worktree orchestration (ROADMAP R-200) behind
  `evaluate_isolated_candidate`: the CLI now requires a clean checked-out baseline,
  evaluates an existing local Candidate branch in a temporary worktree, fast-forwards
  only on KEEP, retains evidence outside the disposable worktree, and removes the
  worktree on success, revert, escalation, or instrument failure. The merge path now
  requires and records authorization issued from completed Worker Pool maker/checker
  state and bound to the exact Candidate branch/commit, rejects Candidate mutations
  made by evaluation probes, and prunes stale worktree registrations. `--record-baseline`
  now re-evaluates and promotes the baseline only after merge. Five real-git lifecycle
  tests cover merge, revert, cleanup, promotion ordering, and unsafe-baseline refusal.
- Implemented Job Store (ROADMAP R-202): `src/recurspec/spec_runner/store.py`, a
  SQLite-backed store for the Runner's durable state (node status, contract hashes,
  atomic claims, TTL'd capability-survey cache, a `tree.json` projection), matching
  `docs/architecture/spec-runner/job-store/SYSTEM.md` exactly. Every write opens its own
  short-lived connection under `BEGIN IMMEDIATE`, so atomic claims are safe across real
  threads/processes without shared connection state. Dirty-propagation reaches a changed
  node and its parent only, never siblings. `rebuild_from_tree` refuses an invalid
  Contract Tree rather than guess, and markdown always wins over a stale stored row.
  11 tests, including a threaded concurrency test run repeatedly to rule out flakiness.
  Two small, genuinely reusable helpers were added to `contract.py` to support this:
  `decision_class()` (parses §8's Decision class) and `resolve_child_path()` (extracted
  from `validate_contract`'s own child-link resolution, now shared instead of duplicated).
- Added `build_tree_index()` to `contract.py`: discovers every node in a valid Contract
  Tree keyed by `node_id`, with `parent_id` resolved. Refactored Job Store's
  `rebuild_from_tree` to use it instead of its own duplicated parent-mapping walk.
- Implemented Context Packer (ROADMAP R-104): `src/recurspec/spec_runner/context_packer.py`.
  Assembles the bounded packet for one node's turn - parent §1+§3, siblings' §3 only
  (never sibling bodies), the node's own current draft, survey context, and a
  byte-identical contract card generated from `design.md` - or refuses with
  `BudgetOverflow` naming the largest contributor rather than truncate. An invalid
  Contract Tree anywhere refuses to pack (`SchemaRejected`) rather than dispatch a worker
  against ground that can't be trusted. Token estimation is an explicitly-labeled
  conservative heuristic (3 chars/token), not a real tokenizer; exact vendor counting was
  pruned as needless dependency work because it does not change the refusal seam. 7 tests,
  including one asserting a grandparent's content never reaches a grandchild's packet.
- Implemented Worker Pool (ROADMAP R-201): `src/recurspec/spec_runner/workers.py`.
  Owns the pool's own policy - phase-to-tier routing, budget enforcement (discards a
  response's body on overflow so a partial spec can never surface as complete),
  maker ≠ checker enforced via a real tracked-state registry (not a prompt instruction),
  and a concurrency cap enforced by a semaphore inside `dispatch` itself, not just its
  `dispatch_many` convenience wrapper. Deliberately does not ship a concrete Claude Agent
  SDK integration: the SDK's package name and version must be read from live
  documentation before pinning it (per the node's own §8), which cannot be verified from
  here, and asserting an unverified pin would violate the project's own evidence policy.
  Callers inject a `RuntimeCall`; the pool's full policy is implemented and tested against
  a fake one. 8 tests, including a concurrency-cap test run repeatedly to rule out
  flakiness. R-201 shipped as `done` without waiting on R-200 (worktree lifecycle) - the
  roadmap's "blocked by" was an assumed build order, not a real technical dependency.
- Consolidated legacy `OW-*` readiness remnants into the sole incomplete-work registry,
  `ROADMAP.md`. Stale references to completed Job Store, Context Packer, and Candidate
  lifecycle work were removed; hypothetical tokenizer integration was rejected rather
  than carried as permanent process debt; the one real unfinished runtime adapter is now
  ROADMAP R-204.

### Fixed

- Recurspec's own `docs/architecture/**/SYSTEM.md` tree now carries `<!-- recurspec-contract:
  1.0 -->` and passes `recurspec contract check docs/architecture` end to end, including
  cross-node interface composition. Previously every node in the tree failed the version
  check released in 0.2.0, so the tool had never actually validated its own architecture.
- Replaced the non-canonical `EvidenceStage: Asserted` value (undefined in the schema and
  absent from `CONTEXT.md`'s vocabulary) with `Unknown` across all affected invariants,
  moving the dropped justification text into the invariant statement instead of discarding
  it.
- Reformatted Interface Contracts sections from Markdown tables to the bulleted
  `- **Inputs:**` / `- **Outputs:**` syntax the Contract Engine parser actually recognizes.
- Added the missing §8 Technology Resolution block to four leaf nodes that lacked one
  (Evaluation Gate, Contract Reconciler, Frontier Adapter, Structure Gate).
- Fixed a Worker Pool invariant that used `MAY` in a `WHILE` clause, violating its own
  declared EARS grammar.
- Added `test_recurspecs_own_architecture_tree_passes_its_own_contract_engine` so this
  cannot silently regress.
- Renamed `docs/architecture/design-runner/` to `docs/architecture/spec-runner/` so the
  directory, the node's own title ("Spec Runner"), and every cross-reference agree; updated
  `ROADMAP.md` and the root `SYSTEM.md` module table accordingly.
- Replaced the planned implementation seams `src/spec_runner/*` and
  `src/technology_resolver/*` — top-level packages that never matched the project's actual
  single-package layout (`src/recurspec/`) — with paths under `src/recurspec/`. The three
  Spec Runner children (context-packer, job-store, worker-pool) are grouped in a
  `src/recurspec/spec_runner/` subpackage, matching their real parent/child relationship in
  the tree instead of scattering as unrelated top-level packages.
- Added `help=` text to every CLI argument across `evaluate`, `skills`, and `contract
  check` (previously only `-h` itself had a description) and switched their formatters to
  `ArgumentDefaultsHelpFormatter` so displayed defaults can't drift from the code. Added
  `test_every_cli_argument_documents_itself` to keep this from regressing.
- Added the missing EARS "Optional" pattern (`WHERE ... SHALL ...`) to `EARS_PATTERNS` and
  the bundled schema's `ears_pattern` enum. `docs/research/foundations.md` has always cited
  this as one of the paper's five patterns (verified against
  [Mavin's own EARS reference](https://alistairmavin.com/ears/)), but the schema only ever
  implemented four, silently renaming the paper's "unwanted behaviour" to `Conditional` with
  no citation note. `Optional` is now accepted; the `Conditional` naming is now explained
  where it's introduced instead of silently diverging from the cited source.
- Fixed the same `EvidenceStage: Asserted` / invented `Checked` value in the two documents
  most likely to actively teach the wrong format going forward: the skill's own worker-facing
  template (`src/recurspec/skill/references/design.md`) and the README-linked worked example
  (`docs/examples/identity-design.md`, since removed). `design.md`'s Evidence Stage table
  now matches the
  schema's real seven-value enum exactly, with a note against inventing new stage labels.
- Found and fixed a real atomic-leaf misclassification bug while wiring R-105 below: the
  parser's leaf detector only recognized a bare `Atomic leaf.` lead-in, so the 8 of 10 real
  architecture nodes that write it as bold and/or annotated Markdown (`**Atomic leaf
  (procured).**`, `(Phase 0)`, etc.) were silently treated as non-leaf. This never produced
  a visible diagnostic before because none of those nodes had ports declared; it surfaced
  the moment real ports were added. `_is_atomic_leaf` now uses one regex tolerant of both
  the bold marker and the parenthetical annotation, replacing two duplicated string-prefix
  checks. Covered by `test_validate_contract_recognizes_a_bold_annotated_atomic_leaf_declaration`.
- Fixed R-600 through R-608, a security/correctness review of the Evaluation Gate, Worker
  Pool, and Contract Engine: a Candidate could no longer replace its own gate probes and
  merge itself; Worker Pool state now proves independent maker/checker approval instead of
  treating any within-budget CHECK response as authorization; invalid or non-finite
  telemetry and evidence-log corruption now fail closed instead of manufacturing evidence;
  hollow and disconnected Contract Trees are rejected; the documented Worker Pool state path
  can no longer make evaluation refuse to start; the bundled skill's references were aligned
  with the shipped CLI and canonical vocabulary; the missing `job-store`/`worker-pool` probe
  scripts were added and the Contract Engine's multi-object `measure.sh` payload was fixed;
  floating dependency versions are rejected in both the inventory and §8 Pin fields; and CLI
  path arguments are now validated against escaping their declared seams. See ROADMAP.md's
  "Review remediation" table for the full ID-by-ID evidence.
- Fixed R-609 through R-616, a follow-up adversarial pass over the R-600–R-608 fixes:
  `checks.sh`/`measure.sh` pinning now also covers the `tests/` tree they shell out to, so a
  Candidate can no longer pass its own checks by weakening the assertions those checks run;
  a produce racing an in-flight CHECK call can no longer authorize content the checker never
  reviewed; evidence-log corruption on a complete (newline-terminated) line, or a non-object
  JSON scalar, now raises instead of being silently forgiven or crashing later with
  `AttributeError`; every bundled probe resolves `python3`/`python` instead of assuming a
  bare `python` alias; the baseline cleanliness check no longer excludes the whole
  `.recurspec/` directory (a tracked dirty file there still blocks evaluation); exact-version
  detection now accepts `v`-prefixed tags, hex revisions, and `algo:hex` digests while
  rejecting malformed pins; a Contract Node §6 declaration can no longer point outside the
  repository; and the bundled skill's one repository-only relative link was removed. See
  ROADMAP.md's "Follow-up hardening" table for the full ID-by-ID evidence.
- Removed `.scratch/wayfinder-map/` (`01-spec-engine.md`, `02-reconciler.md`, `MAP.md`),
  pre-redesign scratch content that stayed committed after the redesign and had drifted
  into a second, contradictory readiness list — banned skill names, a non-existent archive
  reference, and component paths (`src/spec_engine/`, `docs/architecture/spec-engine/`)
  that were never part of the current architecture. `.scratch/` is now gitignored in full
  (previously only `.scratch/handoffs/`), and `test_local_scratch_state_is_never_committed`
  guards against this recurring.
- Fixed R-617 through R-620, a general (non-adversarial) optimization and bug pass: a
  relative `tree_root` passed to `build_tree_index()` silently lost every non-root node's
  `parent_id` instead of resolving it correctly (a path-identity mismatch between an
  unresolved `rglob()` walk and `resolve_child_path()`'s always-resolved output), which
  would have dropped parent context from Context Packer packets and broken the Job Store's
  parent-dirty propagation had either been called with a relative path; the Worker Pool's
  authorization-state file is now written from one place (`_persist_authorizations()`)
  instead of also being independently read-modified-written by `merge_authorization()`,
  which raced concurrent `dispatch()` calls and, even sequentially, went stale the moment
  the next `dispatch()` rewrote the file from its own snapshot and silently dropped
  candidate identity it had just recorded; `JobStore.rebuild_from_tree()` now commits as
  one transaction instead of one per node, so a rebuild is atomic and its overhead no
  longer scales with tree size; and `nodes.status` is now indexed so `claim_next_ready()`
  is no longer a full table scan under concurrent workers. See ROADMAP.md's "Optimization
  and bug pass" table for the full ID-by-ID evidence.
- Corrected the Ernst & Baldassarre Registered Reports citation to *Empirical Software
  Engineering* 28, 55 (2023). The DOI was already right; the volume and year were not.
- Tightened the R-619/R-620 job-store tests: a mid-rebuild upsert failure now has to
  leave the prior store unchanged, and `idx_nodes_status` is asserted on `nodes.status`
  via `PRAGMA index_info`, not just by index name. Job Store and Worker Pool §6 test
  counts were brought in line with the files (14 and 17).

### Fixed

- REVIEW3 remediations R-621–R-626: pin the full `modules/` probe environment into
  Candidate worktrees; reject `1latest` as an exact pin; resolve §6 paths so escaping
  symlinks are unsafe; schema-validate evidence events; bind probes to
  `RECURSPEC_PYTHON`; include the EARS citation inside the installed skill.

### Added

- R-203: `recurspec modules check` maps changed files to measurable modules via §6
  paths and runs those modules' `checks.sh` / `measure.sh`. CI evaluates the diff
  against the pull-request base (or `HEAD^` on push).
- R-303: `recurspec frontier publish|check` writes Research Frontier tickets under
  `.recurspec/frontiers/` and can create a GitHub issue via `gh`. Type B / Wayfinder
  vocabulary is not used.
- R-500: `recurspec corpus export --i-opt-in` writes a redacted decision corpus and
  refuses without the flag.

- R-204: a packet-only Messages-API adapter (`messages_runtime`) behind the Worker Pool
  seam, optional extra `recurspec[runtime]` pinning `anthropic==0.122.0`. Claude Agent
  SDK and OpenAI Agents SDK were surveyed from PyPI and rejected (filesystem tools /
  second scheduler). Survey: `docs/research/r-204-runtime-survey.md`.
- R-404: published non-web Contract Tree at `docs/examples/log-archive` (local log
  rotate + verify).
- Empty R-400–R-403 case-study log template. No outcome data collected.

- `recurspec skills install` now also writes the bundled skill to Grok
  (`$GROK_HOME/skills`, default `~/.grok/skills`). `--target` accepts `grok`; `all`
  still installs every supported consumer. `GROK_HOME` is Grok's documented config-directory
  override, not an invented Recurspec variable.

- The EARS "Complex" pattern (two or more keyword clauses combined in one statement, e.g.
  `WHILE <state>, WHEN <trigger> ... SHALL ...`) is now recognized, per the design
  inference already recorded in `foundations.md` §1 (ROADMAP R-106). A statement tagged
  `[Complex]` must lead with a recognized keyword and genuinely combine at least two of
  them — tagging a single-keyword statement `Complex` is rejected, not silently accepted
  as a loophole. Covered by two new tests, one positive and one negative.
- Declared real machine-checkable ports through the Spec Runner subtree (ROADMAP R-105):
  root now supplies `contract_path`, `max_tokens_per_node`, and `concurrency` as external
  inputs; job-store produces `node_id` and `survey_result`; context-packer consumes both
  plus `max_tokens_per_node` and produces `packet`; worker-pool consumes `packet`,
  `max_tokens_per_node`, and `concurrency`. Every port formalizes a relationship the prose
  already narrated — none invented. The root's other five L1 modules were investigated and
  found to have no real cross-sibling data flow to port (they're independently-invoked CLI
  gates, not a pipeline); they stay prose-only Interface Contracts by documented design.

## [0.2.0] - 2026-08-12

### Added

- Versioned JSON Schema Draft 2020-12 representation for Contract Nodes.
- `recurspec contract check PATH` with stable text/JSON diagnostics and distinct invalid
  contract versus instrument-failure exit codes.
- Contract Engine checks, fixtures, and a correctly labeled `Sampled` acceptance metric.
- Deterministic Contract Tree composition validation for child paths, levels, explicit
  interface ports, missing producers, and dependency cycles.
- Progressive adoption and project-fit guidance for teams that do not need the full loop.

## [0.1.0] - 2026-08-12

### Added

- Installable `recurspec` Python package and CLI.
- One bundled `recurspec` agent skill with internal design, resolution, and
  reconciliation references.
- Tiered Evaluation Gate, explicit baseline promotion, Negative Pattern memory, and
  bounded escalation.
- Cross-platform skill installation for Claude Code and Codex.
- CI, package-build validation, and repository integrity tests.

### Changed

- Consolidated the prototype repository under one Recurspec vocabulary and layout.
- Moved runtime code to `src/recurspec`, tests to `tests`, probes to `modules`, and
  templates to `examples/module`.
- Replaced the historical mixed checklist with a product maturity roadmap.

### Removed

- Conflicting specialist skill names and the Bash-only installer.
- Obsolete archived drafts from the published tree; history remains available in git.
