# Ticket 02 — Implement Multi-Signal Auto-Expander

**Target Spec Node:** [docs/architecture/RECONCILER/SYSTEM.md](file:///C:/Users/dcarn/aiprojects/recursive-system-design/docs/architecture/RECONCILER/SYSTEM.md)  
**Status:** ready-for-agent  
**Blocked by:** None (Frontier)

## What to build
Build `src/reconciler/auto_expander.py` to inspect `.md` line counts and auto-convert bloated specs into directory trees.

## Acceptance Criteria
- [ ] Converts any spec file >150 lines into `dir/SYSTEM.md` + sub-nodes.
- [ ] Emits draft `SYSTEM.md` for unreferenced source files in `/src`.
- [ ] Passing unit tests in `tests/test_reconciler.py`.
