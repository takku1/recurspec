---
name: recursive-spec
description: Recursively decompose a complex system into a hierarchical tree of atomic specifications (SYSTEM.md nodes) using EARS notation down to leaf component contracts, then link them to Wayfinder.
disable-model-invocation: true
---

# Recursive System Specification (RSS)

Decompose any complex system (e.g. Website Search, Game Engine, Auth Pipeline, Profile Page) into a living fractal spec tree before and during implementation.

## Workflow

### 1. Root System Definition (L0)
Ask the user for the overall system vision and create `docs/architecture/SYSTEM.md` (Level 0). Use the `SYSTEM.md` template below.

### 2. EARS Requirements & Invariants
Express all invariants in the `SYSTEM.md` using strict **EARS Notation**:
- **[Ubiquitous]:** `The [System] SHALL [behavior]`
- **[Event-driven]:** `WHEN [trigger] THE SYSTEM SHALL [behavior]`
- **[State-driven]:** `WHILE [state] THE SYSTEM SHALL [behavior]`
- **[Conditional]:** `IF [condition] THEN THE SYSTEM SHALL [behavior]`

### 3. Recursive Decomposition Pass
For each system node, evaluate: *"Can this be divided into distinct sub-components with independent interface seams?"*
- **If YES:** Create a child subdirectory with its own `SYSTEM.md` (e.g., `docs/architecture/SEARCH/QUERY_PIPELINE/SYSTEM.md`) and reference it under `## 2. Sub-System Decomposition`.
- **If NO:** Mark it as an **Atomic Leaf Node** (implementable in a single TDD session).

### 4. Ready-Enough Gate (`doc-readiness.md`)
Do not over-decompose unneeded branches upfront. Create/update `docs/doc-readiness.md` tagging locked core layers as `READY` and future/unclear branches as `FOG_OF_WAR` or `INTENTIONALLY_DEFERRED`.

### 5. Wayfinder Frontier Linkage
For each Atomic Leaf Node:
- Generate a tracer-bullet ticket on the Wayfinder issue tracker map (or local `.scratch` tickets).
- Set the ticket's target URI directly to the leaf `SYSTEM.md`.

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

## 4. Invariants (EARS Notation)
- [Ubiquitous] The component SHALL ...
- [Event-driven] WHEN ... THE SYSTEM SHALL ...
- [State-driven] WHILE ... THE SYSTEM SHALL ...
- [Conditional] IF ... THEN THE SYSTEM SHALL ...

## 5. Architectural Decisions (ADRs)
- **ADR-001:** [Title] — Context, Decision, and Impact.

## 6. Leaf Execution & Test Seam (Leaf Nodes Only)
- **Implementation File(s):** Relative path to source code.
- **Test Surface Seam:** Primary unit/integration test file location.
```
