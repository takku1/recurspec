# Multi-Signal Structural Contract Reconciler

Structural Feedback detail. Module contract: [architecture/contract-reconciler/SYSTEM.md](../architecture/contract-reconciler/SYSTEM.md). Incomplete work is tracked in [ROADMAP.md](../../ROADMAP.md).

---

## Paradigm

Documentation is not a static write-once artifact. Under multi-agent edit rates, the blueprint needs **sensory triggers** that open draft nodes, split bloated contracts, and sync test-introduced seams.

```mermaid
graph TD
    S1[Signal A: Code Drift] --> Agent[Contract Reconciler Observer]
    S2[Signal B: Structural Bloat] --> Agent
    S3[Signal C: Test Seam] --> Agent
    Agent --> Split{Split / Draft?}
    Split -->|File to folder| Sub[Child SYSTEM.md nodes]
    Split -->|Draft leaf| Draft[New leaf under parent]
    Sub --> WF[Wayfinder tickets]
    Draft --> WF
```

Signal D (metric drift) is empirical — owned by Evaluation Gate + Empirical Feedback; tracked as OW-13 until implemented.

---

## Signal A — AST / code drift

- **Trigger:** New source file or exported symbol without a linked architecture node.
- **Action:** Draft `docs/architecture/.../SYSTEM.md` under the best parent; link from parent §2; emit Type A or Type B ticket.
- **Research basis:** Requirements–design–code traceability (RE practice); SDB reject when drift is left unacknowledged at commit (research foundation §2–§3).

---

## Signal B — structural bloat

- **Trigger:** Spec exceeds ~150 lines **or** encodes > 3 distinct responsibilities with separable interfaces.
- **Action:** Convert file node to directory: `NAME.md` → `name/SYSTEM.md` + child nodes; emit child tickets; ADR on the split.
- **Research basis:** Recursive modular decomposition / deep modules (interface vs implementation complexity); ADR hygiene for *why* the split occurred.

---

## Signal C — test seam expansion

- **Trigger:** TDD introduces a mock/adapter not listed in parent interface contracts.
- **Action:** Update parent §3 Inputs/Outputs and related EARS clauses; do not silently expand production coupling.

---

## Example evolution

```
Day 1:  docs/architecture/profile-page/SYSTEM.md   (single leaf)

Day N:  docs/architecture/profile-page/
          SYSTEM.md
          header/SYSTEM.md
          bio-form/SYSTEM.md
          privacy-settings/SYSTEM.md
```

Wayfinder receives child frontier tickets; open-work gains rows only if process infrastructure is incomplete (not for every leaf).

---

## Rules

1. Prefer **interface-driven** splits over arbitrary line cuts.
2. Never invent requirements during auto-draft; mark Epistemic Stage `Unknown` until Architect review.
3. Do not treat reconcile as a substitute for measurement (Empirical Feedback).
