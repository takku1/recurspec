# Spec Engine (Level 1 Component)

## 1. System Intent & Responsibility
Responsible for creating, validating, and formatting `SYSTEM.md` files adhering to EARS notation and contract schemas.

## 2. Sub-System Decomposition
- **Atomic Leaf Component:** No further decomposition required for Phase 0.

## 3. Interface Contracts (Inputs & Outputs)
- **Inputs:** System/sub-system title, intent prose, EARS invariant rules.
- **Outputs:** Validated `SYSTEM.md` Markdown content.

## 4. Invariants (EARS Notation)
- [Ubiquitous] The Spec Engine SHALL format all invariants using EARS notation keywords.
- [Conditional] IF a spec node is an Atomic Leaf THEN THE SYSTEM SHALL include Section 6 (Leaf Execution & Test Seam).

## 5. Architectural Decisions (ADRs)
- **ADR-001:** Enforce strict EARS keywords (Ubiquitous, Event-driven, State-driven, Conditional).

## 6. Leaf Execution & Test Seam
- **Implementation File:** `src/spec_engine/generator.py`
- **Test Surface Seam:** `tests/test_spec_engine.py`
