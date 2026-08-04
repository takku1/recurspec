# Reconciler (Level 1 Component)

## 1. System Intent & Responsibility
Listens for code drift, spec file bloat, and TDD test seams, triggering dynamic file-to-folder auto-expansions.

## 2. Sub-System Decomposition
- **Atomic Leaf Component:** No further decomposition required for Phase 0.

## 3. Interface Contracts (Inputs & Outputs)
- **Inputs:** Workspace file tree, git status, spec file line counts.
- **Outputs:** File-to-folder refactoring actions, updated child spec nodes.

## 4. Invariants (EARS Notation)
- [Event-driven] WHEN a spec file exceeds 150 lines THE SYSTEM SHALL convert it into a directory with a root `SYSTEM.md`.
- [State-driven] WHILE scanning `/src` IF a file is not linked in `/docs/architecture` THE SYSTEM SHALL generate a draft leaf spec.

## 5. Architectural Decisions (ADRs)
- **ADR-001:** 150 lines set as the threshold for automatic file-to-folder decomposition.

## 6. Leaf Execution & Test Seam
- **Implementation File:** `src/reconciler/auto_expander.py`
- **Test Surface Seam:** `tests/test_reconciler.py`
