# Ticket 01 — Implement EARS Spec Engine Generator

**Target Spec Node:** [docs/architecture/SPEC_ENGINE/SYSTEM.md](file:///C:/Users/dcarn/aiprojects/recursive-system-design/docs/architecture/SPEC_ENGINE/SYSTEM.md)  
**Status:** ready-for-agent  
**Blocked by:** None (Frontier)

## What to build
Build `src/spec_engine/generator.py` to parse component intents and format valid EARS `SYSTEM.md` nodes.

## Acceptance Criteria
- [ ] Exports `generate_system_spec(title, intent, invariants, subcomponents)` function.
- [ ] Enforces EARS keywords (`[Ubiquitous]`, `[Event-driven]`, `[State-driven]`, `[Conditional]`).
- [ ] Passing unit tests in `tests/test_spec_engine.py`.
