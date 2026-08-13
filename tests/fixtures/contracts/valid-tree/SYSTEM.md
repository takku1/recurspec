# Example Pipeline (L1)

<!-- recurspec-contract: 1.0 -->

## 1. System Intent & Responsibility

Transform a source into an artifact through independently failing seams.

## 2. Sub-System Decomposition

- [Publish](publish/SYSTEM.md)
- [Transform](transform/SYSTEM.md)

## 3. Interface Contracts

- **Inputs:** `source`
- **Outputs:** `artifact`

## 4. Invariants (EARS + Epistemic Stage)

- **[Ubiquitous]** THE SYSTEM SHALL compose both stages.
  - `EvidenceStage:` Sampled

## 5. Architectural Decisions (ADRs)

- **ADR-001:** Use explicit interface ports.
