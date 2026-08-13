# Publish (L2)

<!-- recurspec-contract: 1.0 -->

## 1. System Intent & Responsibility

Publish a transformed value.

## 2. Sub-System Decomposition

Atomic leaf.

## 3. Interface Contracts

- **Inputs:** `transformed`
- **Outputs:** `artifact`

## 4. Invariants (EARS + Epistemic Stage)

- **[Ubiquitous]** THE SYSTEM SHALL publish an artifact.
  - `EvidenceStage:` Sampled

## 5. Architectural Decisions (ADRs)

- **ADR-001:** Publish through one seam.

## 6. Leaf Execution & Test Seam

- **Implementation Files:** `src/publish.py`.
- **Test Surface Seam:** `tests/test_publish.py`.

## 7. Measurement Seams

- **Primary Metric:** publish acceptance.

## 8. Technology Resolution

- **Decision class:** BUILD
- **Selected:** Python.
