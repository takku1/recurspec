# Wayfinder Connector (Level 1 Component)

## 1. System Intent & Responsibility
Connects atomic leaf specs to the Wayfinder issue tracker map, populating decision/implementation tickets on the active frontier.

## 2. Sub-System Decomposition
- **Atomic Leaf Component:** No further decomposition required for Phase 0.

## 3. Interface Contracts (Inputs & Outputs)
- **Inputs:** Leaf `SYSTEM.md` node paths, issue tracker type (Local / GitHub / Linear).
- **Outputs:** Wayfinder tickets with target URIs set to leaf `SYSTEM.md` files.

## 4. Invariants (EARS Notation)
- [Ubiquitous] The Wayfinder Connector SHALL format every issue title using the project's domain vocabulary.
- [Event-driven] WHEN a new leaf spec is created THE SYSTEM SHALL publish a corresponding ticket to the issue tracker.

## 5. Architectural Decisions (ADRs)
- **ADR-001:** Support `.scratch/wayfinder-map/` as default local markdown tracker.

## 6. Leaf Execution & Test Seam
- **Implementation File:** `src/wayfinder_connector/publisher.py`
- **Test Surface Seam:** `tests/test_wayfinder_connector.py`
