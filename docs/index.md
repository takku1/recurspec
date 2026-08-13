# Recurspec documentation

## Start here

1. [Getting started](./getting-started.md)
2. [Project fit and progressive adoption](./adoption.md)
3. [Canonical language](../CONTEXT.md)
4. [Contract design](./process/contract-design.md)
5. [Worked identity design](./examples/identity-design.md)
6. [Evidence cycle](./process/evidence-cycle.md)

## Design process

| Document | Purpose |
|---|---|
| [Contract design](./process/contract-design.md) | Goal to finite Contract Tree |
| [Stack resolution](./process/stack-resolution.md) | `BUY / ADOPT / WRAP / BUILD / DEFER` gate |
| [Evidence cycle](./process/evidence-cycle.md) | Candidate implementation, evaluation, and repair |
| [Contract reconciliation](./process/contract-reconciliation.md) | Structural and Empirical Feedback into contracts |

## Architecture

The recursive architecture starts at [architecture/SYSTEM.md](./architecture/SYSTEM.md).
Each directory contains one `SYSTEM.md` Contract Node. These documents describe intended
modules and clearly label work that has not yet been implemented.

## Evidence and project status

- [Research foundations](./research/foundations.md) contains source-backed rationale.
- [ROADMAP.md](../ROADMAP.md) is the only incomplete-work registry.
- Historical drafts were removed from the published tree and remain recoverable from git
  history.

## Editing rules

- Use the terms in [CONTEXT.md](../CONTEXT.md).
- Put incomplete work only in [ROADMAP.md](../ROADMAP.md).
- Never promote `Sampled` evidence to `Proved`.
- Never invent a citation, vendor, version, price, or feature claim.
