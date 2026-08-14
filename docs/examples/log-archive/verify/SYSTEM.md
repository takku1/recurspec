# Verify (L1)

<!-- recurspec-contract: 1.0 -->

## 1. System Intent & Responsibility

Hash a written archive and emit a manifest line. Does not rotate the live log.

## 2. Sub-System Decomposition

Atomic leaf.

## 3. Interface Contracts

- **Inputs:** `archive_path`
- **Outputs:** `archive_manifest`

## 4. Invariants (EARS + Epistemic Stage)

- **[Ubiquitous]** THE SYSTEM SHALL refuse to record a manifest line when the archive hash
  cannot be computed.
  - `EvidenceStage:` Sampled

## 5. Architectural Decisions (ADRs)

- **ADR-001:** One archive path in, one manifest record out.

## 6. Leaf Execution & Test Seam

- **Implementation Files:** not shipped — this tree is a published example, not a product.
- **Test Surface Seam:** `tests/test_contract.py::test_log_archive_example_tree_is_a_valid_contract_tree`

## 7. Measurement Seams

- **Primary Metric:** verify refusals on missing files (direction: observation only).

## 8. Technology Resolution

- **Decision class:** BUILD
- **Justification:** Genuinely trivial and stable — one SHA-256 over a file, written as a
  line. No vendor owns "hash this local path."
- **Selected:** Python standard library `hashlib`.
- **Standard / protocol:** SHA-256
- **Alternatives considered:**
  | Option | Why not |
  |--------|---------|
  | md5sum / sha256sum CLI | Platform-specific binaries; the stdlib hash is the portable seam |
- **Fit gap:** no retention/prune policy — out of scope for this example.
- **Seam:** example only; no product module.
- **Exit cost:** LOW
- **Cost model:** local disk only
- **Liability transferred:** none
- **Operational owner:** us
- **Failure mode:** refuse rather than invent a hash
- **Open questions:** none
