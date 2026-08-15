# Contract Engine (L1)

<!-- recurspec-contract: 1.0 -->

## 1. System Intent & Responsibility

Transform a versioned Markdown Contract Node into a normalized, interoperable contract
and deterministic diagnostics. It does not own implementation execution, dependency
resolution, or authoring prose on a user's behalf.

## 2. Sub-System Decomposition

Atomic leaf. The Markdown adapter and JSON Schema validator share one public validation
seam and cannot fail independently from a user's perspective.

## 3. Interface Contracts

- **Inputs:** `contract_path`
  A `SYSTEM.md` file or directory containing Contract Nodes marked with
  `<!-- recurspec-contract: 1.0 -->`.
- **Outputs:** `normalized_contract`, `diagnostics`
  A normalized Contract Node conforming to the bundled JSON Schema and stable
  diagnostics containing path, rule code, and message.
- **Interface syntax:** Section 3 declares machine-checkable ports as backtick identifiers
  on `**Inputs:**` and `**Outputs:**` lines. Descriptive prose remains human context but
  does not create a port.
- **CLI:** `recurspec contract check PATH [--format text|json]`;
  `recurspec status REPO` classifies a repository using this engine plus filesystem facts.
- **Exit status:** `0` valid, `1` contract invalid, `2` validation instrument failed.
  `status` exits `0` after a successful inspection and `2` if the repository cannot be
  read; missing probes change `route`, not the process exit.

## 4. Invariants (EARS + Epistemic Stage)

- **[Ubiquitous]** The Contract Engine SHALL validate normalized Contract Nodes against
  JSON Schema Draft 2020-12.
  - `EvidenceStage:` Sampled
- **[Ubiquitous]** The Contract Engine SHALL report diagnostics in byte-stable order.
  - `EvidenceStage:` Sampled
- **[Conditional]** IF a Contract Node is an Atomic Leaf THEN THE SYSTEM SHALL require
  Sections 6, 7, and 8.
  - `EvidenceStage:` Sampled
- **[Conditional]** IF an invariant lacks a recognized EARS pattern or Evidence Stage
  THEN THE SYSTEM SHALL reject the Contract Node.
  - `EvidenceStage:` Sampled
- **[Conditional]** IF a directory is checked THEN THE SYSTEM SHALL validate every
  recursively discovered `SYSTEM.md` file.
  - `EvidenceStage:` Sampled
- **[Conditional]** IF a non-Atomic Contract Node links children THEN THE SYSTEM SHALL
  require every link to resolve within the checked tree at exactly the next level.
  - `EvidenceStage:` Sampled
- **[Conditional]** IF a child declares an input port THEN THE SYSTEM SHALL require that
  port to be supplied by the parent input boundary or an already satisfiable sibling.
  - `EvidenceStage:` Sampled
- **[Conditional]** IF a parent declares an output port THEN THE SYSTEM SHALL require that
  port to be available after child interface composition reaches a fixed point.
  - `EvidenceStage:` Sampled

## 5. Architectural Decisions (ADRs)

- **ADR-001:** JSON Schema Draft 2020-12 is the portable source of structural truth;
  Python types are adapters, not the public specification.
- **ADR-002:** Version metadata remains an unobtrusive HTML comment so Contract Nodes
  stay readable Markdown and render cleanly on GitHub.
- **ADR-003:** Version 1.0 requires explicit metadata and fails closed; unversioned
  documents are migration candidates, not implicitly valid legacy contracts.
- **ADR-004:** Interface satisfaction uses a deterministic fixed-point traversal over
  explicit port identifiers. This detects missing producers and dependency cycles without
  pretending that prose similarity proves compatibility.
- **ADR-005:** `recurspec status` is a WRAP over this engine plus Structure Gate §7 path
  extraction. It does not move file-existence checks into Markdown validation, because
  `contract check` has no repository root.

## 6. Leaf Execution & Test Seam

- **Implementation Files:** `src/recurspec/contract.py`,
  `src/recurspec/schemas/contract-node-1.0.schema.json`, `src/recurspec/cli.py`,
  `src/recurspec/project_status.py`.
- **Test Surface Seam:** `tests/test_contract.py` through `validate_contract()` and the
  public CLI parser/handler; `tests/test_project_status.py` for repository orientation.

## 7. Measurement Seams

- **Primary Metric:** `valid_fixture_acceptance_rate` (target `1.0`, direction: higher).
- **Tree Metric:** `valid_tree_fixture_acceptance_rate` (target `1.0`, direction: higher).
- **Harness Path:** `modules/contract-engine/measure.sh`.
- **Correctness Backpressure:** `modules/contract-engine/checks.sh`.
- **Telemetry Surface:** stable JSON diagnostic list written to stdout on request.
- **Branching Policy:** isolated Candidate; KEEP only when checks pass, the valid-fixture
  rate is `1.0`, invalid fixtures are rejected, and telemetry is non-contradictory.

## 8. Technology Resolution

- **Decision class:** BUILD
- **Justification:** The Contract Tree normalization, EARS checks, parent/child
  composition, and deterministic diagnostics are Recurspec-specific and substantially
  exceed a thin validator adapter. `jsonschema>=4.26,<5` remains a procured implementation
  dependency for the commodity schema-validation portion.
- **Selected:** Python Contract Engine using JSON Schema Draft 2020-12 for its normalized
  representation.
- **Standard / protocol:** JSON Schema Draft 2020-12.
- **Alternatives considered:**

  | Option | Why not |
  |---|---|
  | Pydantic 2.13.x | Excellent Python validation, but makes Python models the primary contract and adds domain coupling at the interoperability seam. |
  | Pure standard-library validation | Avoids a dependency but would reimplement a mature standard and error traversal. |
  | Python-Markdown 3.10.x | Produces HTML and intentionally does not implement CommonMark; more machinery than the bounded structural adapter needs. |
  | NetworkX 3.6.x | Mature graph algorithms, but unnecessary runtime weight for a deterministic fixed-point traversal over a small Contract Tree. |

- **Fit gap:** JSON Schema cannot parse Markdown, enforce EARS sentence forms, or validate
  composition across Contract Nodes; the adapter owns extraction and tree semantics.
- **Seam:** `src/recurspec/contract.py`.
- **Exit cost:** LOW — replace the validator behind one normalized mapping.
- **Cost model:** No service spend; reconsider only if dependency weight or startup time
  materially dominates the CLI.
- **Liability transferred:** JSON Schema conformance and generic error traversal.
- **Operational owner:** us.
- **Failure mode:** Fail closed with exit `2` when the schema or adapter cannot run; never
  reinterpret an instrument failure as an invalid user contract.
- **Open questions:** none.
