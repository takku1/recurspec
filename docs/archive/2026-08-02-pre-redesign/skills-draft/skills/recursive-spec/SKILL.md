---
name: recursive-spec
description: Recursively decompose a complex system into a hierarchical tree of atomic specifications (SYSTEM.md nodes) using EARS notation with Epistemic Stage tracking and Section 7 Measurement Seams.
disable-model-invocation: true
---

# Recursive System Specification (RSS)

Decompose any complex system into a living fractal spec tree before and during implementation.

## Workflow

### 1. Root System Definition (L0)
Create `docs/architecture/SYSTEM.md` (Level 0). Use the `SYSTEM.md` template below.

### 2. EARS Requirements, Invariants & Epistemic Stages
Express all invariants using strict **EARS Notation** and tag each with its current **Epistemic Stage**:
- **[Ubiquitous]:** `The [System] SHALL [behavior]`
- **[Event-driven]:** `WHEN [trigger] THE SYSTEM SHALL [behavior]`
- **[State-driven]:** `WHILE [state] THE SYSTEM SHALL [behavior]`
- **[Conditional]:** `IF [condition] THEN THE SYSTEM SHALL [behavior]`

**Epistemic Stage Tagging:**
- `[Unknown]` — Asserted without inspection or proof.
- `[Observed]` — Directly verified in syntax/AST.
- `[Sampled]` — Verified by unit tests/mock probes (high false positive potential; non-promotable to Proved).
- `[Inferred]` — Structural pattern match.
- `[Measured]` — Hardware-benchmarked with variance tracking (`measure.sh`).
- `[Proved]` — Formally verified by solver (Z3/SMT) or algebraic rule.
- `[Refuted]` — Contradicted by counterexample.

### 3. Recursive Decomposition Pass
Evaluate: *"Can this node be divided into distinct sub-components with independent interface seams?"*
- **If YES:** Create child directory with `SYSTEM.md`.
- **If NO:** Mark as **Atomic Leaf Node** and complete Section 6 (Test Seam) and Section 7 (Measurement Seams).

### 4. Ready-Enough Gate (`doc-readiness.md`)
Maintain `docs/doc-readiness.md` across 3 axes: `Depth` (L0-L3), `Domain`, and `Maturity` (`READY`, `FOG_OF_WAR`, `INTENTIONALLY_DEFERRED`).

### 5. Wayfinder Frontier Linkage
Generate tracer-bullet tickets on Wayfinder. Type A for known architecture, Type B for open research/prototype frontiers.

---

## `SYSTEM.md` Template

```markdown
# [Component Name] (Level N)

## 1. System Intent & Responsibility
High-level purpose and architectural role of this component node.

## 2. Sub-System Decomposition
- **[Child Component 1](./CHILD_1/SYSTEM.md)** — Role and interface boundary.
- **[Child Component 2](./CHILD_2/SYSTEM.md)** — Role and interface boundary.

## 3. Interface Contracts (Inputs & Outputs)
- **Inputs:** Types, events, configuration, or state passed in.
- **Outputs:** Returned data, events emitted, state mutations.

## 4. Invariants (EARS Notation + Epistemic Stage)
- [Ubiquitous] The component SHALL ...
  - `EvidenceStage:` Observed | Sampled | Measured | Proved
- [Event-driven] WHEN ... THE SYSTEM SHALL ...
  - `EvidenceStage:` Observed | Sampled | Measured | Proved
- [State-driven] WHILE ... THE SYSTEM SHALL ...
  - `EvidenceStage:` Observed | Sampled | Measured | Proved
- [Conditional] IF ... THEN THE SYSTEM SHALL ...
  - `EvidenceStage:` Observed | Sampled | Measured | Proved

## 5. Architectural Decisions (ADRs)
- **ADR-001:** [Title] — Context, Decision, and Impact.

## 6. Leaf Execution & Test Seam (Leaf Nodes Only)
- **Implementation File(s):** Relative path to source code.
- **Test Surface Seam:** Primary unit/integration test file location (`checks.sh` target).

## 7. Measurement Seams (Leaf Nodes Only)
- **Primary Metric:** `[metric_name]` (e.g. `latency_p99_ms`, target ≤ N)
- **Harness Path:** `components/[COMPONENT_NAME]/measure.sh`
- **Correctness Backpressure:** `components/[COMPONENT_NAME]/checks.sh`
- **Telemetry Surface:** Structured JSON schema for self-diagnostics
- **Branching Policy:** Worktree hypothesis branch; merge authorized only when checks pass AND primary metric improves AND no telemetry contradiction
```
