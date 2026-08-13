# Changelog

All notable changes follow [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Added

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
  (`docs/examples/identity-design.md`). `design.md`'s Evidence Stage table now matches the
  schema's real seven-value enum exactly, with a note against inventing new stage labels.
- Found and fixed a real atomic-leaf misclassification bug while wiring R-105 below: the
  parser's leaf detector only recognized a bare `Atomic leaf.` lead-in, so the 8 of 10 real
  architecture nodes that write it as bold and/or annotated Markdown (`**Atomic leaf
  (procured).**`, `(Phase 0)`, etc.) were silently treated as non-leaf. This never produced
  a visible diagnostic before because none of those nodes had ports declared; it surfaced
  the moment real ports were added. `_is_atomic_leaf` now uses one regex tolerant of both
  the bold marker and the parenthetical annotation, replacing two duplicated string-prefix
  checks. Covered by `test_validate_contract_recognizes_a_bold_annotated_atomic_leaf_declaration`.

### Added

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
