# Technology Resolver (L1)

> Process detail: [technology-resolution.md](../../process/technology-resolution.md) ·
> [decomposition-loop.md](../../process/decomposition-loop.md) ·
> Worked example: [examples/login-decomposition.md](../../examples/login-decomposition.md)

## 1. System Intent & Responsibility

Assign every spec node a **decision class** (BUY / ADOPT / WRAP / BUILD / DEFER), select a
concrete technology for procured nodes, and emit the §8 Technology Resolution block. Owns
the third-party-first bias and the **stopping rule** for recursive decomposition: a node
resolved to BUY or ADOPT is terminal.

**Does not own:** the decomposition itself (Spec Engine), ticket publication (Wayfinder
Connector), or runtime dependency installation. It produces decisions and their evidence,
not lockfiles.

## 2. Sub-System Decomposition

**Atomic leaf (Phase 0).** Candidate later split — only once interfaces stabilise:
CapabilitySurveyor (research) | ClassScorer (the six axes) | ResolutionWriter (§8 emit) |
StalenessAuditor (review triggers).

## 3. Interface Contracts

| | |
|--|--|
| **Inputs** | Node responsibility statement; non-goals; constraints (budget, scale, compliance regime, existing stack); survey results from `/research` |
| **Outputs** | Decision class; selected product + pin; alternatives table with reasons; fit gap; seam path; exit cost; cost model; liability transfer; §8 block; DEFER → Type B ticket intent |

## 4. Invariants (EARS + Epistemic Stage)

- **[Ubiquitous]** The Resolver SHALL assign exactly one decision class to every node
  before that node is decomposed or specified.
  - `EvidenceStage:` Observed (process rule)
- **[Ubiquitous]** The Resolver SHALL treat BUILD as the class requiring recorded
  justification; BUY, ADOPT, and WRAP need no defence beyond their §8 block.
  - `EvidenceStage:` Observed
- **[Conditional]** IF a node resolves to BUY or ADOPT THEN THE SYSTEM SHALL mark it
  terminal and SHALL NOT decompose the vendor's internals.
  - `EvidenceStage:` Observed — this is the loop's termination guarantee
- **[Conditional]** IF a node's parts would resolve to differing decision classes THEN
  THE SYSTEM SHALL split the node at that boundary.
  - `EvidenceStage:` Inferred — a procurement boundary is a real interface seam
- **[Conditional]** IF the capability survey cannot be completed from primary sources
  THEN THE SYSTEM SHALL resolve `DEFER` and emit a Type B ticket, and SHALL NOT guess a
  vendor.
  - `EvidenceStage:` Observed — same no-fabrication rule as [research foundation](../../research/foundation.md)
- **[Event-driven]** WHEN a §8 pinned version diverges from the project lockfile THE
  SYSTEM SHALL raise a Back-Channel A drift signal.
  - `EvidenceStage:` Unknown · *Open:* OW-06
- **[State-driven]** WHILE a WRAP adapter grows beyond its seam THE SYSTEM SHALL treat
  the growth as a bloat signal and re-open the resolution.
  - `EvidenceStage:` Unknown · *Open:* OW-07

## 5. Architectural Decisions (ADRs)

- **ADR-001:** Five decision classes, not binary build/buy. WRAP is named explicitly
  because it is the most common real outcome and the one flat plans omit — buying a
  capability still leaves an adapter, and that adapter is the swap point.
- **ADR-002:** Procurement terminates recursion. Without this the tree has no natural
  floor and "decompose further" runs to absurdity (login → OIDC → JWT → RSA). Subtree
  depth then measures how much you are building, which is the number worth seeing.
- **ADR-003:** Split at non-uniform resolution. Choosing the BUY/BUILD fault line as the
  seam is not arbitrary — you cannot refactor across a vendor's API, so the boundary is
  already real.
- **ADR-004:** Alternatives and their rejection reasons are retained in §8 permanently.
  The record is what stops the same debate recurring every time someone new reads the node.
- **ADR-005:** Prefer options speaking a standard protocol (OIDC, SMTP, S3, OTel) so the
  seam stays swappable. Proprietary APIs are permitted but must record exit cost.

## 6. Leaf Execution & Test Seam

- **Implementation:** `src/technology_resolver/resolver.py`
- **Tests:** `tests/test_technology_resolver.py` — must cover: §8 completeness validation,
  DEFER on incomplete survey, refusal to emit a vendor without a source
- **Open work:** OW-06, OW-07

## 7. Measurement Seams

- **Primary metric:** `resolution_completeness` — fraction of terminal nodes whose §8 has
  every required field populated (target 1.0, direction `higher`)
- **Secondary:** `build_class_ratio` — share of terminal nodes classed BUILD. Not a target
  to minimise blindly; a sharp rise is a signal the survey phase is being skipped
- **Harness:** `components/technology-resolver/measure.sh`
- **Backpressure:** `components/technology-resolver/checks.sh`
- **Telemetry:** per-node `{class, has_alternatives, has_exit_cost, survey_sources}`
- **Branching:** worktree hypothesis; keep only on checks pass ∧ no completeness regression

## 8. Technology Resolution

*(Dogfooded — this node runs its own gate.)*

- **Decision class:** BUILD
- **Justification:** Differentiator. The gate encodes RSS's own method; no vendor sells
  "decide build-vs-buy inside a recursive spec tree". Everything it *depends* on is
  procured (see below).
- **Selected:** Python module driven by the `/resolve-stack` skill; §8 blocks are Markdown
  in `SYSTEM.md`, not a separate database
- **Alternatives considered:**
  | Option | Why not |
  |--------|---------|
  | ADR tooling (adr-tools, Log4brains) | Records decisions but does not gate them, and is not tied to a spec tree |
  | Architecture-decision SaaS | Decisions leave the repo; cannot be reviewed in a diff alongside the code they govern |
  | SBOM / dependency scanners | Answer "what is installed", not "what should we use and why" — complementary, not substitute |
- **Fit gap:** n/a (custom by intent)
- **Seam:** `src/technology_resolver/` — the spec tree only sees emitted §8 blocks
- **Exit cost:** n/a
- **Cost model:** our engineering time
- **Liability transferred:** none
- **Operational owner:** us
- **Failure mode:** a wrong or stale resolution ships a bad dependency. Mitigated by
  retained alternatives (§5 ADR-004) and the review triggers in the process doc
- **Open questions:** OW-06 (lockfile drift detection), OW-07 (adapter bloat signal)
