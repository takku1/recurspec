# Changelog

All notable changes follow [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

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
