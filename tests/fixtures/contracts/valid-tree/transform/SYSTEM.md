# Transform (L2)

<!-- recurspec-contract: 1.0 -->

## 1. System Intent & Responsibility

Transform a source value.

## 2. Sub-System Decomposition

Atomic leaf.

## 3. Interface Contracts

- **Inputs:** `source`
- **Outputs:** `transformed`

## 4. Invariants (EARS + Epistemic Stage)

- **[Ubiquitous]** THE SYSTEM SHALL transform the source.
  - `EvidenceStage:` Sampled

## 5. Architectural Decisions (ADRs)

- **ADR-001:** Transform through one seam.

## 6. Leaf Execution & Test Seam

- **Implementation Files:** `src/transform.py`.
- **Test Surface Seam:** `tests/test_transform.py`.

## 7. Measurement Seams

- **Primary Metric:** transform acceptance.

## 8. Technology Resolution

- **Decision class:** BUILD
- **Selected:** Python.
