# Changelog

All notable changes follow [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

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
