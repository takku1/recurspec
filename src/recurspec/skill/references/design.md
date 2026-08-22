# Contract Design

Take a goal — "a booking site", "a CLI that syncs X" — and produce a tree of nodes each
specified well enough that an implementing agent needs no further decisions.

The failure this exists to prevent: a flat plan whose every line is the same size on the
page and wildly different in reality, where `- Login and user accounts` sits beside
`- CSS` and an agent responds by hand-rolling a credential store.

## Existing architecture documents

`recurspec status` reports `not_recurspec` when `SYSTEM.md` files exist without
`<!-- recurspec-contract: 1.0 -->`. That is a missing Recurspec Contract Tree, not a
finished design.

- Read those files as source material for FRAME.
- Do not treat their headings, crate maps, or process prose as §1–§8.
- Do not add the version marker until the node meets the template below.
- Create root `ROADMAP.md`. If `FEATURE_GAPS.md` or another incomplete-work file already
  lists work, index those IDs into `ROADMAP.md`; do not keep Recurspec debt only there.

A second Contract Tree may live at `.recurspec/contracts` (for example a hygiene
overhaul next to the product tree). `recurspec status` classifies it separately. Do not
merge two roots into one composition check.

Do not name `modules/<leaf>/checks.sh` or `measure.sh` in §7 until those files exist.
`status` reports missing declared probes and routes `repair`.

A paper, skill-install, or literature-review request is not a reason to skip
`recurspec status` on the subject repository. It is a reason not to invent a Contract
Tree for a folder that only holds prose.

Evidence Stage (Unknown … Proved) is maturity. A passing test suite is executed
behavior: it licenses "the exercised cases satisfied their oracles," not "the system
achieves its goal." Do not promote Sampled tests to an outcome claim. If no
comparative study exists, write the claim boundary instead of a performance sentence.

## The discovery loop — run only as deep as the next safe decision requires

### 1. FRAME

One sentence of responsibility, plus explicit non-goals.

- Frame the **capability**, not the implementation: *"prove a visitor controls an
  identity"*, not *"users table"*. Naming an implementation here pre-commits you to
  building it.
- If the sentence needs an "and", that is the first evidence the node splits.
- A numbered or bulleted list of deliverables is not one FRAME. Split it (`recurspec
  fanout`) and run this loop on each item with only that item's packet. Sibling items
  stay out of the implementor context.

### 2. COVERAGE REVIEW — look for what the first frame missed

Treat the current decomposition as a hypothesis, not a complete inventory.

- Look **vertically** for missing children, requirements, failure modes, measurements,
  and research inside the node.
- Look **horizontally** for missing or contradictory interfaces between siblings.
- Inspect only relevant **sibling pairs** for high-impact behavior that emerges at an
  interaction seam. Higher-order combinations require an explicit risk justification.
- Classify every proposal `Unknown` or `Inferred`, state why it matters, and identify the
  evidence that would confirm it. Do not make prevalence claims without a real corpus.

Coverage Review produces proposals for Architect review, never an automatic Contract Tree
mutation. Irrelevant, optional, or weakly supported features are discarded; unresolved
high-impact uncertainty becomes a Research Frontier in `ROADMAP.md`.

### 3. RESEARCH — before decomposing, ask if it already exists

Survey managed services, OSS libraries, and framework-native features. Produce **at least
two real alternatives** with versions or plan tiers, plus what each does *not* cover.

- Use `/research` for anything unfamiliar. Verify against **live documentation** — library
  and pricing facts age badly, and a stack chosen from stale recall is how a project
  adopts a deprecated SDK on day one.
- Never invent a vendor, version, or price. A survey you cannot complete resolves `DEFER`.

### 4. RESOLVE — assign exactly one decision class

`BUY` · `ADOPT` · `WRAP` · `BUILD` · `DEFER`. Their definitions, the six-axis score, and
the survey they rest on are in [resolve.md](resolve.md) — follow it rather than deciding
from these names alone.

**BUILD carries the burden of proof.** It is correct only when the node is your
differentiator, the fit gap is fatal, cost inverts at your scale, the dependency is a
liability, or the thing is genuinely trivial and stable. Record which. The other classes
need no defence beyond their §8 block.

Two questions settle most nodes:

- **Commodity or differentiator?** If you cannot name a way a user would notice you built
  it better, it is a commodity — BUY or ADOPT.
- **What does building it make you liable for?** Credential storage, card data, PII, email
  deliverability. Buying moves that obligation to someone whose business is meeting it.

Prefer options that speak a **standard** (OIDC, SMTP, S3, OpenTelemetry, SQL) and put the
WRAP adapter on the standard, not on proprietary extensions.

### 5. TEST — terminal, or split?

**Split where the decision class stops being uniform.** If part of the node would be
bought and part built, that boundary *is* the seam — you cannot refactor across a
vendor's API, so it is already a real interface.

Terminal when:

| Because | Condition |
|---------|-----------|
| **Procured** | Uniformly BUY/ADOPT → spec the *seam*, never the vendor's internals |
| **Atomic build** | BUILD/WRAP implementable in one TDD session against one test seam |
| **Deferred** | DEFER → Research Frontier; subtree resumes when it closes |

Must decompose when parts resolve to **different** classes, or when uniformly BUILD but
too large for one session.

**Do not decompose past a procurement boundary.** Once identity verification resolves to a
managed IdP, you do not then spec OIDC, JWT signing, and RSA. That is the termination
guarantee — and subtree depth then honestly measures how much you are building.

### 6. SPECIFY

Terminal nodes get the full template below **including §8**. Non-terminal nodes get
§1–§5 plus a child index.

---

## Depth guards

1. **Max depth 4** (L0→L3) by default; deeper needs an ADR on the node.
2. **Procurement terminates.**
3. **Distinct failure mode:** a child that cannot fail independently of its siblings is a
   step in a procedure, not a module.
4. **Two-child minimum:** one child is a rename, not a decomposition — collapse it.
5. **No speculative children:** fog goes to `ROADMAP.md` as a Research Frontier, not
   into invented nodes.

Expect **shallow where the world has solved it, deep where you are actually building**. A
uniformly deep tree means RESEARCH is being skipped.

---

## Invariants — EARS + Epistemic Stage

Every invariant uses an EARS pattern and carries an evidence tag. These are the five
patterns from Mavin, A., Wilkinson, P., Harwood, A., and Novak, M. (2009),
*Easy Approach to Requirements Syntax (EARS)*, 17th IEEE International Requirements
Engineering Conference, pp. 317-322, https://doi.org/10.1109/RE.2009.9.
`Conditional` is Recurspec's label for what that paper calls *unwanted behaviour* —
the IF/THEN form is used here for any conditional response, not only error paths.

- **[Ubiquitous]** `The [System] SHALL [behavior]`
- **[Event-driven]** `WHEN [trigger] THE SYSTEM SHALL [behavior]`
- **[State-driven]** `WHILE [state] THE SYSTEM SHALL [behavior]`
- **[Conditional]** `IF [condition] THEN THE SYSTEM SHALL [behavior]`
- **[Optional]** `WHERE [feature is included] THE SYSTEM SHALL [behavior]`
- **[Complex]** two or more of the above keyword clauses combined in one statement, e.g.
  `WHILE [state], WHEN [trigger] THE SYSTEM SHALL [behavior]`. Must genuinely combine at
  least two keywords — tagging a single-keyword statement `Complex` is rejected.

| Stage | Meaning |
|-------|---------|
| `Unknown` | Declared without inspection |
| `Observed` | Verified in syntax/AST |
| `Sampled` | Unit tests / mock probes — **never** promotable to Proved |
| `Inferred` | Structural pattern match |
| `Measured` | Hardware-benchmarked with variance (`measure.sh`) |
| `Proved` | Solver (Z3/SMT) or algebraic rule |
| `Refuted` | Contradicted by counterexample |

These seven are the complete, exhaustive set the schema accepts — do not invent another
label (e.g. `Asserted`, `Checked`); `Unknown` is the correct stage for a declared-but-
unverified claim.

---

## Incomplete-work gate

Maintain **one** checklist: `ROADMAP.md` (`ready` | `blocked` | `deferred` |
`research`). Completed history belongs in release notes and git. Do not create parallel
readiness or uncertainty lists. A DEFER node
becomes a Research Frontier entry there — an uncertainty that must be resolved before
the node can be completed.

---

## `SYSTEM.md` template

```markdown
# [Module Name] (L<level>)

<!-- recurspec-contract: 1.0 -->

## 1. System Intent & Responsibility
Single-sentence responsibility. Explicit non-goals ("does not own: ...").

## 2. Sub-System Decomposition
Atomic leaf (procured | atomic build | deferred).
<!-- Non-terminals replace this with child links and omit §6–§8. -->

## 3. Interface Contracts
- **Inputs:** types, events, configuration, state passed in.
- **Outputs:** returned data, events emitted, state mutations.

## 4. Invariants (EARS + Epistemic Stage)
- **[Ubiquitous]** THE SYSTEM SHALL ...
  - `EvidenceStage:` Unknown

## 5. Architectural Decisions (ADRs)
- **ADR-001:** [Title] — context, decision, impact.

## 6. Leaf Execution & Test Seam (terminal nodes only)
- **Implementation Files:** relative path to source.
- **Test Surface Seam:** primary test file (`checks.sh` target).

## 7. Measurement Seams (terminal nodes only)
- **Primary Metric:** `[metric_name]` (target, and `direction: lower|higher`)
- **Evaluation Gate:** `modules/[name]/measure.sh`
- **Correctness Backpressure:** `modules/[name]/checks.sh`
- **Telemetry Surface:** structured JSON for self-diagnostics
- **Branching Policy:** worktree candidate; merge only when checks pass AND the primary
  metric does not regress AND no telemetry contradiction

## 8. Technology Resolution (terminal nodes only)
- **Decision class:** BUY | ADOPT | WRAP | BUILD | DEFER
- **Justification:** BUILD only — which of the five BUILD conditions applies
- **Selected:** product / library, pinned version or plan tier
- **Standard / protocol:** OIDC, SMTP, S3, none
- **Alternatives considered:**
  | Option | Why not |
  |--------|---------|
  | ... | specific reason — cost, fit gap, licence, maturity |
- **Fit gap:** what it does NOT cover  <!-- this is where child nodes come from -->
- **Seam:** path to the adapter/module isolating it
- **Exit cost:** LOW | MEDIUM | HIGH — what swapping actually requires
- **Cost model:** pricing at expected scale; the number that would change the decision
- **Liability transferred:** obligations moved to the vendor
- **Operational owner:** vendor | us
- **Failure mode:** behaviour when it is down, and the fallback
- **Open questions:** ROADMAP R-nnn / Research Frontier, or "none"
```

A `BUILD` with no recorded justification is the failure this gate exists to catch. Field
wording is parsed by `recurspec stack check`; keep it identical to
[resolve.md](resolve.md) §5.

---

## Finishing

1. Every terminal node has §6, §7, §8 complete.
2. Every DEFER has a Research Frontier entry in `ROADMAP.md`.
3. `ROADMAP.md` reflects product incompleteness (not one row per leaf).
4. Report the shape: node count, depth, and the **BUILD ratio** — how much of this you are
   actually writing. A high ratio early is the signal to re-run RESEARCH.
