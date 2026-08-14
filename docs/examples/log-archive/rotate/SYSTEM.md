# Rotate (L1)

<!-- recurspec-contract: 1.0 -->

## 1. System Intent & Responsibility

Copy a live log file into a dated archive path and truncate the live file. Does not
checksum the archive or decide retention.

## 2. Sub-System Decomposition

Atomic leaf.

## 3. Interface Contracts

- **Inputs:** `log_path`
- **Outputs:** `archive_path`

## 4. Invariants (EARS + Epistemic Stage)

- **[Ubiquitous]** THE SYSTEM SHALL write a new archive without deleting unverified history.
  - `EvidenceStage:` Sampled

## 5. Architectural Decisions (ADRs)

- **ADR-001:** One file in, one archive path out.

## 6. Leaf Execution & Test Seam

- **Implementation Files:** not shipped — this tree is a published example, not a product.
- **Test Surface Seam:** `tests/test_contract.py::test_log_archive_example_tree_is_a_valid_contract_tree`

## 7. Measurement Seams

- **Primary Metric:** archives written per invocation (direction: observation only).

## 8. Technology Resolution

- **Decision class:** BUILD
- **Justification:** Genuinely trivial and stable — copy, date-stamp, truncate — with no
  liability that a log-shipping vendor would take on for a laptop/host CLI.
- **Selected:** Python standard library `pathlib` + `shutil`.
- **Standard / protocol:** none
- **Alternatives considered:**
  | Option | Why not |
  |--------|---------|
  | logrotate | Host-packaged, not portable onto Windows without a POSIX layer Recurspec already refuses to assume |
  | Vector / Fluent Bit | Ship-and-forward agents; this leaf only archives locally |
- **Fit gap:** no checksum — owned by Verify.
- **Seam:** example only; no product module.
- **Exit cost:** LOW
- **Cost model:** local disk only
- **Liability transferred:** none
- **Operational owner:** us
- **Failure mode:** refuse to truncate if the archive write fails
- **Open questions:** none
