---
name: dual-loop
description: Enforce Outer Strategy / Inner Tactical agent separation. Author strategy packets, dispatch TDD inner-loop sessions in isolated worktrees, and run empirical Auditor verification without authority drift.
disable-model-invocation: true
---

# Dual-Loop Protocol (Outer Strategy / Inner Execution)

Prevent **authority drift** (where an implementing agent grades its own homework or alters specification contracts) by strictly separating the **Architect/Auditor (Outer Loop)** from the **Implementor (Inner Loop)**.

## Role Separation & Authority Matrix

| Role | Environment | Permissions | Can Edit Specs? | Can Mutate Code? |
|---|---|---|---|---|
| **Architect / Auditor** | Outer Loop | Full repo context, graphgraph, Sherloc, worktree manager | ✅ YES | ❌ NO (Strategy/Harness only) |
| **Implementor** | Inner Loop (Isolated Worktree) | Reads Strategy Packet ONLY; `/tdd` execution | ❌ NO | ✅ YES (Source & Unit Tests) |

---

## Outer Loop Workflow

### 1. Author Strategy Packet
When claiming a Wayfinder leaf ticket, the Outer Loop Architect generates a bounded Strategy Packet at `.scratch/handoffs/strategy-<ticket-id>.md`:

```markdown
# Strategy Packet: [Leaf Ticket Name]

## Target Spec Node
`docs/architecture/[PATH]/SYSTEM.md`

## 1. Goal & Boundaries
- Specific leaf behavior to implement.
- What is explicitly OUT of scope.

## 2. Invariants to Satisfy (EARS Notation)
- [Ubiquitous/Event-driven/State-driven/Conditional] ...

## 3. Test Seams (§6)
- File under test: `src/...`
- Test location: `tests/...`

## 4. Measurement Seam Baseline (§7)
- Baseline metric: `[name] = [value]`
- Backpressure harness: `components/[NAME]/checks.sh`
```

### 2. Dispatch Inner Loop (Implementor)
Run the Implementor agent in an isolated worktree branch (`hypothesis/<ticket-id>`). The Implementor executes `/tdd` against the Strategy Packet.

### 3. Outer Loop Verification Gate (Auditor)
Upon Implementor "done" signal, the Auditor steps in on the Outer Loop:
1. **Run Correctness Backpressure:** `bash components/[NAME]/checks.sh`
2. **Run Empirical Measurement:** `bash components/[NAME]/measure.sh` (with ablation checks if optimizing)
3. **Validate Telemetry Instrument:** Run `/graybox` validation checks
4. **Sherloc Audit:** Evaluate evidence stage (`Sampled` → `Measured` / `Proved`)
5. **Decision:**
   - **PASS:** Merge worktree to main branch; update SYSTEM.md §7 baseline & EvidenceStage tags; trigger Back-Channel A & B reconciliation; close Wayfinder ticket.
   - **FAIL:** Revert worktree; generate **Correction Packet** at `.scratch/handoffs/correction-<ticket-id>.md` and dispatch repair pass.
