# Ticket 02 — Implement Multi-Signal Auto-Expander

**Target Spec Node:** [docs/architecture/reconciler/SYSTEM.md](../../docs/architecture/reconciler/SYSTEM.md)  
**Open work:** OW-02  
**Status:** ready-for-agent  
**Blocked by:** None  

> Archive reference: `docs/archive/2026-08-02-pre-redesign/scratch-wayfinder/wayfinder-map/02-reconciler.md`  
> Process: [docs/process/multi-signal-reconciler.md](../../docs/process/multi-signal-reconciler.md)

## What to build

Build `src/reconciler/auto_expander.py` to inspect line counts / responsibility bloat and auto-convert bloated specs into directory trees; draft leaves for unlinked source files.

## Acceptance Criteria

- [ ] Converts bloated spec files into `dir/SYSTEM.md` + child nodes per policy.
- [ ] Emits draft `SYSTEM.md` (Epistemic Stage `Unknown`) for unreferenced source files under `/src`.
- [ ] Does not invent product requirements beyond structural drafts.
- [ ] Passing unit tests in `tests/test_reconciler.py`.
