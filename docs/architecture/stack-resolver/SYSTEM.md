# Stack Resolver (L1)

<!-- recurspec-contract: 1.0 -->

> Process detail: [stack-resolution.md](../../process/stack-resolution.md) ·
> [contract-design.md](../../process/contract-design.md)

## 1. System Intent & Responsibility

Assign every Contract Node a **decision class** (BUY / ADOPT / WRAP / BUILD / DEFER), select a
concrete technology for procured nodes, and emit the §8 Technology Resolution block. Owns
the third-party-first bias and the **stopping rule** for recursive decomposition: a node
resolved to BUY or ADOPT is terminal.

**Does not own:** the decomposition itself (Contract Engine), ticket publication (Frontier
Adapter), or runtime dependency installation. It produces decisions and their evidence,
not lockfiles.

## 2. Sub-System Decomposition

**Atomic leaf (Phase 0).** Candidate later split — only once interfaces stabilise:
CapabilitySurveyor (research) | ClassScorer (the six axes) | ResolutionWriter (§8 emit) |
StalenessAuditor (review triggers).

## 3. Interface Contracts

- **Inputs:** Node responsibility statement; non-goals; constraints (budget, scale,
  compliance regime, existing stack); survey results from /research; Contract Tree;
  optional authoritative dependency inventory; WRAP line threshold.
- **Outputs:** Decision class; selected product + pin; alternatives table with reasons;
  fit gap; seam path; exit cost; cost model; liability transfer; §8 block; DEFER →
  Research Frontier intent.

## 4. Invariants (EARS + Epistemic Stage)

- **[Ubiquitous]** The Resolver SHALL assign exactly one decision class to every node
  before that node is decomposed or specified. (process rule)
  - `EvidenceStage:` Unknown
- **[Ubiquitous]** The Resolver SHALL treat BUILD as the class requiring recorded
  justification; BUY, ADOPT, and WRAP need no defence beyond their §8 block.
  - `EvidenceStage:` Unknown
- **[Conditional]** IF a node resolves to BUY or ADOPT THEN THE SYSTEM SHALL mark it
  terminal and SHALL NOT decompose the vendor's internals. (this is the loop's
  termination guarantee)
  - `EvidenceStage:` Unknown
- **[Conditional]** IF a node's parts would resolve to differing decision classes THEN
  THE SYSTEM SHALL split the node at that boundary. (a procurement boundary is a real
  interface seam)
  - `EvidenceStage:` Unknown
- **[Conditional]** IF the capability survey cannot be completed from primary sources
  THEN THE SYSTEM SHALL resolve `DEFER` and record a Research Frontier, and SHALL NOT
  guess a vendor. (`test_resolution_audit_reports_incomplete_fields_and_refuses_vendor_on_defer`)
  - `EvidenceStage:` Sampled
- **[Event-driven]** WHEN a §8 pinned version diverges from the project lockfile THE
  SYSTEM SHALL raise a Structural Feedback drift signal.
  (`test_resolution_audit_detects_pin_drift_against_authoritative_inventory`)
  - `EvidenceStage:` Sampled
- **[Conditional]** IF an external BUY, ADOPT, or WRAP pin has no authoritative dependency
  inventory THEN THE SYSTEM SHALL report the audit as indeterminate and SHALL NOT infer a
  current version. (`test_resolution_audit_is_indeterminate_without_inventory_for_an_external_pin`)
  - `EvidenceStage:` Sampled
- **[Conditional]** IF a terminal §8 block omits a required field THEN THE SYSTEM SHALL
  emit a completeness diagnostic. (`test_resolution_audit_reports_incomplete_fields_and_refuses_vendor_on_defer`)
  - `EvidenceStage:` Sampled
- **[State-driven]** WHILE a WRAP adapter grows beyond its seam THE SYSTEM SHALL treat
  the growth as a bloat signal and re-open the resolution.
  (`test_resolution_audit_reopens_a_wrap_that_spreads_past_or_outgrows_its_seam`)
  - `EvidenceStage:` Sampled
- **[Conditional]** IF a WRAP omits its adapter namespace THEN THE SYSTEM SHALL refuse to
  claim complete growth detection; files found inside that namespace but outside the seam
  SHALL re-open the resolution. (`test_resolution_audit_reopens_a_wrap_that_spreads_past_or_outgrows_its_seam`)
  - `EvidenceStage:` Sampled
- **[Ubiquitous]** The `version` grammar SHALL accept semver and PEP 440 exact releases
  alike, so an installed `.postN`, `.devN`, pre-release, or four-component version is not
  misread as floating. (`test_dependency_inventory_accepts_ecosystem_valid_exact_forms`)
  - `EvidenceStage:` Sampled
- **[Optional]** WHERE a §8 Pin declares a Reference kind (`version` | `tag` | `commit` |
  `digest`) THE SYSTEM SHALL validate the pin against only that kind's grammar instead
  of accepting any of the three; an unrecognized kind or a pin that does not match its
  declared kind SHALL be reported, not silently accepted through the blended check.
  Absent a declaration, the ecosystem-neutral blended check is unchanged.
  (`test_resolution_audit_accepts_a_pin_matching_its_declared_reference_kind`,
  `test_resolution_audit_rejects_a_pin_that_does_not_match_its_declared_reference_kind`,
  `test_resolution_audit_rejects_an_unrecognized_reference_kind`)
  - `EvidenceStage:` Sampled

## 5. Architectural Decisions (ADRs)

- **ADR-001:** Five decision classes, not binary build/buy. WRAP is named because it is
  the common real outcome flat plans omit: buying still leaves an adapter, and that
  adapter is the swap point.
- **ADR-002:** Procurement terminates recursion; without a floor, "decompose further"
  runs to absurdity (login → OIDC → JWT → RSA).
- **ADR-003:** Split at non-uniform resolution: you cannot refactor across a vendor's
  API, so the BUY/BUILD fault line is already a real boundary.
- **ADR-004:** Alternatives and rejection reasons stay in §8 permanently; the record is
  what stops the same debate recurring.
- **ADR-005:** Prefer a standard protocol (OIDC, SMTP, S3, OTel) so the seam stays
  swappable; proprietary APIs are permitted but must record exit cost.
- **ADR-006:** Reference kind is opt-in, and `version`/`tag` share one grammar: no single
  regex separates a package version, a VCS tag, a commit, and a digest. Declaring a kind
  narrows validation to that grammar; a bare tag is still not verified as immutable
  (Recurspec cannot ask the vendor), and that residual ambiguity is accepted, not hidden.

## 6. Leaf Execution & Test Seam

- **Implementation:** `src/recurspec/technology_resolver.py`; public seam
  `audit_resolutions()`.
- **Tests:** `tests/test_technology_resolver.py`, plus CLI coverage in `tests/test_cli.py`.

## 7. Measurement Seams

- **Primary metric:** `resolution_completeness` — fraction of terminal nodes whose §8 has
  every required field populated (target 1.0, direction `higher`)
- **Secondary:** `build_class_ratio` — share of terminal nodes classed BUILD. Not a target
  to minimise blindly; a sharp rise is a signal the survey phase is being skipped
- **Evaluation Gate:** `modules/stack-resolver/measure.sh`
- **Backpressure:** `modules/stack-resolver/checks.sh`
- **Telemetry:** per-node `{class, has_alternatives, has_exit_cost, survey_sources}`
- **Audit telemetry:** `{completeness, diagnostics, indeterminate, valid}` with stable
  diagnostic codes for field, pin, inventory, and WRAP seam failures.
- **Branching:** worktree candidate; keep only on checks pass ∧ no completeness regression

## 8. Technology Resolution

*(Dogfooded — this node runs its own gate.)*

- **Decision class:** BUILD
- **Justification:** Differentiator. The gate encodes Recurspec's own method; no vendor sells
  "decide build-vs-buy inside a recursive spec tree". Everything it *depends* on is
  procured (see below).
- **Selected:** Python module driven by the `/recurspec` skill; §8 blocks are Markdown
  in `SYSTEM.md`, not a separate database
- **Standard / protocol:** Contract Node 1.0 Markdown and an explicit JSON dependency
  inventory mapping normalized package names to exact versions.
- **Alternatives considered:**
  | Option | Why not |
  |--------|---------|
  | ADR tooling (adr-tools, Log4brains) | Records decisions but does not gate them, and is not tied to a spec tree |
  | Architecture-decision SaaS | Decisions leave the repo; cannot be reviewed in a diff alongside the code they govern |
  | SBOM / dependency scanners | Answer "what is installed", not "what should we use and why" — complementary, not substitute |
- **Fit gap:** n/a (custom by intent)
- **Seam:** `src/recurspec/technology_resolver.py` — the Contract Tree only sees §8 audit diagnostics.
- **Exit cost:** n/a
- **Cost model:** our engineering time
- **Liability transferred:** none
- **Operational owner:** us
- **Failure mode:** a wrong or stale resolution ships a bad dependency. Mitigated by
  retained alternatives (§5 ADR-004) and the review triggers in the process doc
- **Open questions:** none.
