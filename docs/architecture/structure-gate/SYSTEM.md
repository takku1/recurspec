# Structure Gate (L1)

<!-- recurspec-contract: 1.0 -->

> Research: SDB / dual-state verification — [research/foundations.md](../../research/foundations.md) §2–§3, §5 (L2 rule/schema)

## 1. System Intent & Responsibility

Deterministic **L2** gate: language adapters enforce zero-drift and seam coverage
between code and the Contract Tree. The default adapter is Python's standard-library
`ast`. An optional Rust adapter (`recurspec[rust]`) is omitted, not guessed, when
its dependency is missing. Rejects commits that would land stochastic agent output
without structural verification.

## 2. Sub-System Decomposition

**Atomic leaf (Phase 0).** Later: SpecCoverageCheck | ExportTestSeamCheck | PolicyPack — when each has independent config seams.

## 3. Interface Contracts

- **Inputs:** repository root, source root, Contract Tree root, optional changed-file list.
- **Outputs:** immutable result with sorted diagnostics; JSON/text CLI output and non-zero
  exit on drift or instrument failure.

## 4. Invariants (EARS + Epistemic Stage)

- **[Ubiquitous]** The Gatekeeper SHALL verify that exported symbols intended as seams
  belong to a Contract Node and that declared implementation/test paths exist.
  (`test_structure_gate_accepts_contract_owned_python_with_a_real_test_surface`)
  - `EvidenceStage:` Sampled
- **[Conditional]** IF no source root is supplied THEN THE SYSTEM SHALL infer the one
  the repository layout implies, and SHALL refuse with an ambiguity diagnostic naming
  `--source-root` when the layout implies more than one.
  (`test_source_root_is_inferred_from_the_repository_layout`,
  `test_ambiguous_source_root_fails_closed_naming_the_flag`)
  - `EvidenceStage:` Sampled
- **[Conditional]** IF a Contract Node §7 names a `checks.sh` or `measure.sh` path THEN
  THE SYSTEM SHALL require that file to exist inside the repository.
  (`test_structure_gate_reports_a_missing_declared_probe`)
  - `EvidenceStage:` Sampled
- **[Conditional]** IF a module declares literal `__all__` exports THEN THE SYSTEM SHALL
  use that set as its public surface; every owned exported surface SHALL have a declared
  test seam. (`test_structure_gate_uses_explicit_exports_and_requires_their_test_surface`)
  - `EvidenceStage:` Sampled
- **[Conditional]** IF un-specced code drift is detected under active policy THEN THE SYSTEM SHALL exit non-zero.
  (`test_structure_gate_reports_each_public_symbol_in_an_uncontracted_source_file`)
  - `EvidenceStage:` Sampled
- **[Ubiquitous]** The Gatekeeper SHALL NOT use L4 model-judge scores as a substitute for L1/L2 results. ([research foundation](../../research/foundations.md) §5)
  - `EvidenceStage:` Unknown
- **[Conditional]** IF the rust extra is importable THEN THE SYSTEM SHALL treat top-level
  `pub` items as the public Rust surface and SHALL exclude `#[cfg(test)]` modules;
  IF the extra is missing THEN THE SYSTEM SHALL omit the adapter instead of failing.
  (`test_rust_adapter_detects_pub_items_and_skips_cfg_test`,
  `test_available_adapters_omits_rust_when_the_extra_is_missing`)
  - `EvidenceStage:` Sampled

## 5. Architectural Decisions (ADRs)

- **ADR-001:** Derive implementation ownership and test surfaces from Contract Node §6,
  and declared evaluation probes from §7; do not maintain a parallel structure-policy file.
- **ADR-003:** Extract public symbols through a `LanguageAdapter` seam. Python uses the
  standard-library AST. Rust, when `recurspec[rust]` is installed, uses tree-sitter.
  Extensions without an importable adapter are ignored, not guessed.
- **ADR-002:** Gatekeeper is Auditor-side infrastructure; Implementor may run it locally but cannot waive failures without Outer Loop.

## 6. Leaf Execution & Test Seam

- **Implementation:** `src/recurspec/structure_gate.py`; public seams
  `check_structure()`, `infer_source_root()`, and `source_root_candidates()`.
- **Tests:** `tests/test_structure_gate.py` plus CLI coverage in `tests/test_cli.py`.

## 7. Measurement Seams

- **Primary metric:** `gate_false_negative_rate` on seeded drift fixtures (target → 0 on fixture set)
- **Evaluation Gate / checks:** `modules/structure-gate/measure.sh`, `checks.sh`

## 8. Technology Resolution

- **Decision class:** BUILD
- **Justification:** The ownership policy that joins source paths to Contract Node §6
  is Recurspec-specific. Language parsers are commodities: Python's standard-library
  `ast` is already present; Rust parsing is an optional ADOPT of tree-sitter.
- **Selected:** Python `ast` for `*.py`; optional `tree-sitter` + `tree-sitter-rust`
  via extra `recurspec[rust]` for `*.rs`.
- **Standard / protocol:** Python AST; tree-sitter 0.23–0.26; Contract Node 1.0 Markdown §6.
- **Alternatives considered:**

  | Option | Why not |
  |---|---|
  | Interactive `graphgraph` / `code-review-graph` tooling | Not an installable runtime dependency or stable package protocol; would make the CLI environment-dependent. |
  | A generic dependency-cruiser-style tool | Enforces import boundaries, not "does this symbol have a parent Contract Node," which needs the tree as ground truth. |
  | Hand-rolled Rust regex | Fragile on macros, multi-line signatures, and attributes — a correctness gate cannot guess. |
  | `syn` via a Rust subprocess | Adds a Rust toolchain Recurspec itself does not otherwise need. |

- **Fit gap:** neither `ast` nor tree-sitter knows a Contract Tree, required test seam,
  or §7 probe scripts; the adapter owns §6 path extraction, §7 script extraction,
  ownership joins, and deterministic diagnostics.
- **Seam:** `src/recurspec/structure_gate.py`.
- **Exit cost:** LOW — symbol extraction is isolated behind `LanguageAdapter`.
- **Cost model:** no service spend; local compute only. Rust support is opt-in.
- **Liability transferred:** Python parsing correctness; tree-sitter/tree-sitter-rust
  parse trees when the extra is installed.
- **Operational owner:** us.
- **Failure mode:** a false negative lets un-specced drift land; measured directly by the
  primary metric above. A missing rust extra skips `*.rs` instead of failing closed.
- **Open questions:** none.
