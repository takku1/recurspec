---
name: recursive-spec
description: Recursively decompose a complex system into a hierarchical tree of atomic specifications (SYSTEM.md nodes) down to leaf implementation units, then wire them into Wayfinder.
disable-model-invocation: true
---

# Recursive System Specification (RSS)

Decompose any complex feature, system, or architecture (e.g., website search dropdown, game engine subsystem) into a fractal spec tree before or alongside implementation.

## Workflow

1. **Root System Definition:** Ask the user for the high-level system scope and create `docs/architecture/SYSTEM.md` (Level 0).
2. **Recursive Decomposition Pass:**
   - For each system/subsystem, evaluate: *"Can this be divided into distinct sub-components with independent interfaces?"*
   - If yes: create a child subdirectory with its own `SYSTEM.md` and link it in the parent's `Sub-System Decomposition` section.
   - Repeat recursively until every bottom node is an **Atomic Leaf** (implementable in a single agent session).
3. **Interface Contracts:** Define clear Inputs, Outputs, and Invariants for each leaf node.
4. **Wayfinder Hand-off:**
   - Invoke `/to-tickets` or `/wayfinder` to generate implementation/decision tickets for each Leaf Node.
   - Order execution from Leaf Nodes upward (or via tracer-bullet vertical slices).
5. **Living Spec Maintenance:**
   - When `/implement` or `/tdd` updates a leaf module's API or invariants, immediately sync changes back to its `SYSTEM.md`.
