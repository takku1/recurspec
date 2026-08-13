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

## 1.0: machine-checkable contracts

| ID | Outcome | Status | Blocked by | Contract |
|---|---|---|---|---|
| R-100 | Define a versioned schema for `SYSTEM.md` Contract Nodes | done | — | [Contract Engine](./docs/architecture/contract-engine/SYSTEM.md) |
| R-101 | Validate EARS invariants, Evidence Stages, and terminal §6–§8 sections | done | R-100 | [Contract Engine](./docs/architecture/contract-engine/SYSTEM.md) |
| R-102 | Validate parent/child interface satisfaction | ready | R-100 | [Contract Engine](./docs/architecture/contract-engine/SYSTEM.md) |
| R-103 | Detect stale dependency pins and incomplete technology resolutions | ready | R-100 | [Stack Resolver](./docs/architecture/stack-resolver/SYSTEM.md) |
| R-104 | Generate a byte-stable, bounded worker contract card | ready | R-100 | [Context Packer](./docs/architecture/design-runner/context-packer/SYSTEM.md) |

## 2.0: isolated execution

| ID | Outcome | Status | Blocked by | Contract |
|---|---|---|---|---|
| R-200 | Create, evaluate, merge, and dispose Candidate worktrees | ready | R-101 | [Evaluation Gate](./docs/architecture/evaluation-gate/SYSTEM.md) |
| R-201 | Enforce maker/checker identity separation in state, not prompts alone | ready | R-200 | [Worker Pool](./docs/architecture/design-runner/worker-pool/SYSTEM.md) |
| R-202 | Persist atomic claims and re-derive state from Markdown | ready | R-100 | [Job Store](./docs/architecture/design-runner/job-store/SYSTEM.md) |
| R-203 | Add CI that runs checks and evaluates changed measurable modules | deferred | R-200 | [Evaluation Gate](./docs/architecture/evaluation-gate/SYSTEM.md) |

## 3.0: closed-loop reconciliation

| ID | Outcome | Status | Blocked by | Contract |
|---|---|---|---|---|
| R-300 | Detect uncontracted public symbols and structural drift | ready | R-101 | [Structure Gate](./docs/architecture/structure-gate/SYSTEM.md) |
| R-301 | Turn Structural and Empirical Feedback into draft contract changes | ready | R-300 | [Contract Reconciler](./docs/architecture/contract-reconciler/SYSTEM.md) |
| R-302 | Detect adapters that outgrow their procurement seams | ready | R-300 | [Stack Resolver](./docs/architecture/stack-resolver/SYSTEM.md) |
| R-303 | Publish Research Frontiers to local and remote trackers | deferred | R-301 | [Frontier Adapter](./docs/architecture/frontier-adapter/SYSTEM.md) |

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
| R-405 | Pre-register evaluation metrics and analysis | research | Public protocol before collecting outcome data |

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
