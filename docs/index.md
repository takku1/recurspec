# Recurspec documentation

Recurspec's internal control law is
`DISCOVER -> RESOLVE -> EXECUTE -> CHECK -> RECONCILE`. The documents below each own one
layer of detail; the bundled skill loads them only when its current route requires them.

## Start here

1. [Getting started](./getting-started.md)
2. [Project fit and progressive adoption](./adoption.md)
3. [Canonical language](../CONTEXT.md)
4. [Contract design](./process/contract-design.md)
5. [Published Contract Tree example](./examples/log-archive/SYSTEM.md)
6. [Evidence cycle and adaptive planning](./process/evidence-cycle.md)

## Design process

| Document | Purpose |
|---|---|
| [Contract design](./process/contract-design.md) | Goal to finite Contract Tree |
| [Stack resolution](./process/stack-resolution.md) | `BUY / ADOPT / WRAP / BUILD / DEFER` gate |
| [Evidence cycle](./process/evidence-cycle.md) | Adaptive planning, Candidate authority, evaluation, and repair |
| [Contract reconciliation](./process/contract-reconciliation.md) | Typed findings into reviewable code/contract/work proposals |

## Architecture

The recursive architecture starts at [architecture/SYSTEM.md](./architecture/SYSTEM.md).
Each directory contains one `SYSTEM.md` Contract Node. Implementation and test seams are
declared in §6; incomplete work is recorded only in `ROADMAP.md`.

## Evidence and project status

- [Research foundations](./research/foundations.md) contains source-backed rationale.
- [Constrained-creativity survey](./research/constrained-creativity.md) bounds what the
  supporting literature does and does not license.
- [Evaluation protocol](./research/evaluation-protocol.md) is the pre-registered plan for
  R-400–R-403; it commits to metrics and analysis before any outcome data exists.
- [Case-study log](./research/case-study-log.md) is the empty apparatus for those studies.
- [R-400 case record: graphgraph / DX-WDAC-01](./research/r-400-case-record-graphgraph-dx-wdac-01.md)
  is an observational record from a real ticket. It is explicitly **not** R-400 outcome
  data -- no matched arm, no pre-assignment -- and does not count toward the stopping rule.
- [Log-archive example](./examples/log-archive/SYSTEM.md) is the published non-web
  Contract Tree (R-404).
- [R-204 runtime survey](./research/r-204-runtime-survey.md) is the primary-source
  resolution behind the Worker Pool adapter.

Project orientation: `recurspec status`. Common read-only inspection: `recurspec check`.
Specialized probes and research interfaces remain discoverable through
`recurspec --help`.
- [ROADMAP.md](../ROADMAP.md) is the only incomplete-work registry.
- Historical drafts were removed from the published tree and remain recoverable from git
  history.

## Editing rules

- Use the terms in [CONTEXT.md](../CONTEXT.md).
- Put incomplete work only in [ROADMAP.md](../ROADMAP.md).
- Never promote `Sampled` evidence to `Proved`.
- Never invent a citation, vendor, version, price, or feature claim.
