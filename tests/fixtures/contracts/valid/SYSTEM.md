# Example Contract (L2)

<!-- recurspec-contract: 1.0 -->

## 1. System Intent & Responsibility

Demonstrate a complete Atomic Leaf Contract Node.

## 2. Sub-System Decomposition

Atomic leaf.

## 3. Interface Contracts

- **Inputs:** Markdown.
- **Outputs:** Diagnostics.

## 4. Invariants (EARS + Epistemic Stage)

- **[Ubiquitous]** THE SYSTEM SHALL emit deterministic diagnostics.
  - `EvidenceStage:` Sampled

## 5. Architectural Decisions (ADRs)

- **ADR-001:** Use a public validation seam.

## 6. Leaf Execution & Test Seam

- **Implementation Files:** `src/example.py`.
- **Test Surface Seam:** `tests/test_example.py`.

## 7. Measurement Seams

- **Primary Metric:** valid fixture acceptance rate.

## 8. Technology Resolution

- **Decision class:** BUILD
- **Selected:** Python.
