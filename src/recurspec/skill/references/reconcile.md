# Contract Reconciliation

Inspect the repository for structural drift (Structural Feedback) and empirical behavior drift (Empirical Feedback), automatically auto-healing the spec tree and updating baseline contracts.

## Sensory Signals & Self-Healing Protocol

### Signal A: AST Code Drift (Structural Feedback)
- **Protocol:** Query `graphgraph` context (`query_class="blast_radius"`, scope=`/src`) and `code-review-graph` (`detect_changes` + `get_impact_radius`) to scan `/src` for new or un-specced symbols.
- **Action:** Generate draft leaf `SYSTEM.md` node and link it into parent container.

### Signal B: Structural Bloat Threshold (Structural Feedback)
- **Trigger:** Single spec file exceeds ~150 lines or >3 distinct responsibilities.
- **Action:** Convert file to folder `module/SYSTEM.md`, split out child sub-system specs, append ADR, and emit Wayfinder tickets.

### Signal C: Test Seam Expansion (Structural Feedback)
- **Trigger:** TDD introduces new mocks/adapters/seams.
- **Action:** Sync new external seams back to parent `SYSTEM.md` Section 3 & 6.

### Signal D: Metric Drift & Telemetry Contradiction (Empirical Feedback)
- **Trigger:** `.recurspec/evidence/<module>/log.jsonl` shows primary metric regression > 20% tolerance, or telemetry self-contradiction is detected.
- **Action:**
  1. Flag module in `SYSTEM.md` §7 as "Performance Regressed" or "Instrument Broken".
  2. Append ADR in `SYSTEM.md` documenting metric drift.
  3. Execute Sherloc `Serendipity` pivot: emit Wayfinder Type B `research` ticket to investigate root cause.
  4. Block merge authorizations until ticket resolves.

## Verification Gate
Ensure zero un-specced files remain, all invariants have updated `EvidenceStage` tags, and `.recurspec/evidence/` logs reflect green correctness backpressure.
