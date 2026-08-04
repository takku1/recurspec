# Wayfinder Map — Recursive System Specification Engine

**Label:** `wayfinder:map`  
**Status:** Active Execution Frontier

> Pre-redesign copy: `docs/archive/2026-08-02-pre-redesign/scratch-wayfinder/wayfinder-map/`  
> Process incomplete work (not tickets): [docs/open-work.md](../../docs/open-work.md)

## Destination

Build and verify the five L1 leaf components so the framework can self-heal and expand with dual back-channels.

## Notes

- Skills: `/recursive-spec`, `/reconcile-spec`, `/dual-loop`, `/wayfinder`, `/tdd`, `/code-review`
- Each ticket targets a kebab-case `SYSTEM.md` under `docs/architecture/`

## Decisions so far

- ADR-001: Five-component L1 architecture (Spec Engine, Reconciler, Wayfinder Connector, AST Gatekeeper, Measurement Harness) — [docs/architecture/SYSTEM.md](../../docs/architecture/SYSTEM.md)
- ADR-003: kebab-case architecture directories; archive retains SCREAMING_CASE snapshot
- ADR-004: Research claims require real citations in `docs/research/foundation.md`

## Open Frontier Tickets (Claimable)

- [ ] **[01-spec-engine]** Implement EARS Spec Engine Generator — OW-01  
  - **Target:** [docs/architecture/spec-engine/SYSTEM.md](../../docs/architecture/spec-engine/SYSTEM.md)  
  - **Blocked By:** None

- [ ] **[02-reconciler]** Implement Multi-Signal Auto-Expander — OW-02  
  - **Target:** [docs/architecture/reconciler/SYSTEM.md](../../docs/architecture/reconciler/SYSTEM.md)  
  - **Blocked By:** None

- [ ] **[03-wayfinder-connector]** Implement Ticket Publisher — OW-03  
  - **Target:** [docs/architecture/wayfinder-connector/SYSTEM.md](../../docs/architecture/wayfinder-connector/SYSTEM.md)  
  - **Blocked By:** `01-spec-engine`

- [ ] **[04-ast-gatekeeper]** Implement Zero-Drift Checker — OW-04  
  - **Target:** [docs/architecture/ast-gatekeeper/SYSTEM.md](../../docs/architecture/ast-gatekeeper/SYSTEM.md)  
  - **Blocked By:** `02-reconciler`

- [ ] **[05-measurement-harness]** Implement Branching Measurement Harness — OW-05  
  - **Target:** [docs/architecture/measurement-harness/SYSTEM.md](../../docs/architecture/measurement-harness/SYSTEM.md)  
  - **Blocked By:** `04-ast-gatekeeper`  
  - **Design:** [docs/process/dual-backchannel-loop.md](../../docs/process/dual-backchannel-loop.md)

## Fog of war → open-work only

Do not grow fog lists here. Track deferred process items in [docs/open-work.md](../../docs/open-work.md) (OW-10+).

## Out of scope

- Web GUI for non-dev spec editing (markdown/CLI first)
