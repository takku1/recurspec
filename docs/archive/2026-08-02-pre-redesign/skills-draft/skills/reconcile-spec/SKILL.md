---
name: reconcile-spec
description: Reconcile code changes and empirical measurement telemetry with the specification tree. Handles Code Drift, Spec Bloat, Test Seams, and Metric Drift (Back-Channels A & B).
disable-model-invocation: false
---

# Reconcile Spec (Dual Back-Channel Self-Healing Engine)

Inspect the repository for structural drift (Back-Channel A) and empirical behavior drift (Back-Channel B), automatically auto-healing the spec tree and updating baseline contracts.

## Sensory Signals & Self-Healing Protocol

### Signal A: AST Code Drift (Back-Channel A)
- **Protocol:** Query `graphgraph` context (`query_class="blast_radius"`, scope=`/src`) and `code-review-graph` (`detect_changes` + `get_impact_radius`) to scan `/src` for new or un-specced symbols.
- **Action:** Generate draft leaf `SYSTEM.md` node and link it into parent container.

### Signal B: Structural Bloat Threshold (Back-Channel A)
- **Trigger:** Single spec file exceeds ~150 lines or >3 distinct responsibilities.
- **Action:** Convert file to folder `component/SYSTEM.md`, split out child sub-system specs, append ADR, and emit Wayfinder tickets.

### Signal C: Test Seam Expansion (Back-Channel A)
- **Trigger:** TDD introduces new mocks/adapters/seams.
- **Action:** Sync new external seams back to parent `SYSTEM.md` Section 3 & 6.

### Signal D: Metric Drift & Telemetry Contradiction (Back-Channel B)
- **Trigger:** `.measure/<component>/log.jsonl` shows primary metric regression > 20% tolerance, or telemetry self-contradiction is detected.
- **Action:**
  1. Flag component in `SYSTEM.md` §7 as "Performance Regressed" or "Instrument Broken".
  2. Append ADR in `SYSTEM.md` documenting metric drift.
  3. Execute Sherloc `Serendipity` pivot: emit Wayfinder Type B `research` ticket to investigate root cause.
  4. Block merge authorizations until ticket resolves.

## Verification Gate
Ensure zero un-specced files remain, all invariants have updated `EvidenceStage` tags, and `.measure/` logs reflect green correctness backpressure.
