---
name: reconcile-spec
description: Reconcile code changes with the specification tree. Detects un-specced files, triggers file-to-folder spec auto-expansion, and syncs test seams back to SYSTEM.md contracts.
disable-model-invocation: false
---

# Reconcile Spec (Multi-Signal Self-Healing Engine)

Inspect the repository for code drift, spec bloat, and interface seam changes, then automatically auto-heal and expand the spec tree.

## Workflow

### 1. Detect Un-specced Code Files (Code Drift Signal)
- Use git status, `graphgraph`, or AST tools to scan `/src` for new source files.
- Verify if each source file is referenced by a `SYSTEM.md` node under `/docs/architecture`.
- **If missing:** Generate a draft leaf `SYSTEM.md` node and link it into the nearest parent container.

### 2. Check Spec Bloat Threshold (File-to-Folder Auto-Expansion)
- Scan all `SYSTEM.md` or `.md` files in `/docs/architecture`.
- **Trigger:** If a single spec file exceeds ~150 lines or defines >3 distinct sub-responsibilities:
  1. Convert `component.md` into `component/SYSTEM.md`.
  2. Recursively split out child sub-system specs (e.g. `component/sub_a/SYSTEM.md`, `component/sub_b/SYSTEM.md`).
  3. Append an ADR entry in `component/SYSTEM.md` documenting the split.
  4. Emit corresponding decision/implementation tickets to the Wayfinder issue tracker map.

### 3. Sync Test Seams & Invariants (TDD Reconciliation)
- Check recent test files or mocks created during TDD.
- If new external adapters or interface seams were introduced, update the corresponding leaf `SYSTEM.md` contracts and EARS invariants.

### 4. Gate Verification
- Run a check to ensure zero un-specced files remain and that all leaf contracts are green.
