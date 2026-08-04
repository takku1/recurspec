# Ticket 01 — Implement EARS Spec Engine Generator

**Target Spec Node:** [docs/architecture/spec-engine/SYSTEM.md](../../docs/architecture/spec-engine/SYSTEM.md)  
**Open work:** OW-01  
**Status:** ready-for-agent  
**Blocked by:** None  

> Archive reference: `docs/archive/2026-08-02-pre-redesign/scratch-wayfinder/wayfinder-map/01-spec-engine.md`

## What to build

Build `src/spec_engine/generator.py` to parse component intents and format valid EARS `SYSTEM.md` nodes (including Epistemic Stages and leaf §6/§7 when applicable).

## Acceptance Criteria

- [ ] Exports `generate_system_spec(title, intent, invariants, subcomponents)` (or equivalent clear API).
- [ ] Enforces EARS keywords (`[Ubiquitous]`, `[Event-driven]`, `[State-driven]`, `[Conditional]`).
- [ ] Flags missing Epistemic Stage as `Unknown`.
- [ ] Passing unit tests in `tests/test_spec_engine.py`.
