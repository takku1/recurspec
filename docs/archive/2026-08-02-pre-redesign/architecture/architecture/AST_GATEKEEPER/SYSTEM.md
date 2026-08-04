# AST Gatekeeper (Level 1 Component)

## 1. System Intent & Responsibility
Runs AST analysis via `code-review-graph` / `graphgraph` to enforce pre-commit zero-drift checks between code seams and spec tree contracts.

## 2. Sub-System Decomposition
- **Atomic Leaf Component:** No further decomposition required for Phase 0.

## 3. Interface Contracts (Inputs & Outputs)
- **Inputs:** Source code AST, spec tree node contracts.
- **Outputs:** Verification status (PASS/FAIL) and drift diagnostics.

## 4. Invariants (EARS Notation)
- [Ubiquitous] The AST Gatekeeper SHALL verify that every exported symbol has a corresponding test seam.
- [Conditional] IF un-specced code drift is detected THEN THE SYSTEM SHALL exit with non-zero error code.

## 5. Architectural Decisions (ADRs)
- **ADR-001:** Interface seam coverage checked via `code-review-graph` AST index.

## 6. Leaf Execution & Test Seam
- **Implementation File:** `src/ast_gatekeeper/checker.py`
- **Test Surface Seam:** `tests/test_ast_gatekeeper.py`
