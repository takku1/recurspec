# Local log archive (L0)

<!-- recurspec-contract: 1.0 -->

A published Contract Tree for a CLI/systems pipeline, not a web app. Its delivery is
recorded as R-404 in `CHANGELOG.md`.
This tree is an example of Recurspec applied outside Recurspec itself. It is not a
case-study outcome and carries no R-400–R-403 data.

## 1. System Intent & Responsibility

Rotate incoming host log files into dated archives and verify each archive before it
is retained. Does not ship logs off-box, parse application messages, or serve a UI.

## 2. Sub-System Decomposition

- [Rotate](rotate/SYSTEM.md)
- [Verify](verify/SYSTEM.md)

## 3. Interface Contracts

- **Inputs:** `log_path`
- **Outputs:** `archive_manifest`

## 4. Invariants (EARS + Epistemic Stage)

- **[Ubiquitous]** THE SYSTEM SHALL archive and verify through independently failing seams.
  - `EvidenceStage:` Sampled

## 5. Architectural Decisions (ADRs)

- **ADR-001:** Split rotate from verify so a bad checksum cannot be hidden inside the
  writer that produced the bytes.
