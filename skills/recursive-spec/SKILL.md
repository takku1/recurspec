---
name: recursive-spec
description: Turn a goal into a tree of fully-specified buildable components. Recursively decomposes, resolves each node to a concrete technology (preferring existing services/libraries over custom code), and stops at procurement or one-session build boundaries. Emits SYSTEM.md nodes with EARS invariants, Epistemic Stages, test/measurement seams, and a full tech stack per leaf.
disable-model-invocation: true
---

# Recursive System Specification

Take a goal — "a booking site", "a CLI that syncs X" — and produce a tree of nodes each
specified well enough that an implementing agent needs no further decisions.

The failure this exists to prevent: a flat plan whose every line is the same size on the
page and wildly different in reality, where `- Login and user accounts` sits beside
`- CSS` and an agent responds by hand-rolling a credential store.

Process detail: `docs/process/decomposition-loop.md` ·
Gate criteria: `docs/process/technology-resolution.md` ·
Worked example: `docs/examples/login-decomposition.md`

---

## The loop — run for every node, at every depth

### 1. FRAME

One sentence of responsibility, plus explicit non-goals.

- Frame the **capability**, not the implementation: *"prove a visitor controls an
  identity"*, not *"users table"*. Naming an implementation here pre-commits you to
  building it.
- If the sentence needs an "and", that is the first evidence the node splits.

### 2. RESEARCH — before decomposing, ask if it already exists

Survey managed services, OSS libraries, and framework-native features. Produce **at least
two real alternatives** with versions or plan tiers, plus what each does *not* cover.

- Use `/research` for anything unfamiliar. Verify against **live documentation** — library
  and pricing facts age badly, and a stack chosen from stale recall is how a project
  adopts a deprecated SDK on day one.
- Never invent a vendor, version, or price. A survey you cannot complete resolves `DEFER`.

### 3. RESOLVE — assign exactly one decision class

| Class | Meaning |
|-------|---------|
| **BUY** | Managed third-party service |
| **ADOPT** | OSS library / framework feature you run |
| **WRAP** | Thin adapter you write over a BUY/ADOPT |
| **BUILD** | Genuinely custom |
| **DEFER** | Unresolved → Type B Wayfinder ticket |

**BUILD carries the burden of proof.** It is correct only when the node is your
differentiator, the fit gap is fatal, cost inverts at your scale, the dependency is a
liability, or the thing is genuinely trivial and stable. Record which.

Two questions settle most nodes:

- **Commodity or differentiator?** If you cannot name a way a user would notice you built
  it better, it is a commodity — BUY or ADOPT.
- **What does building it make you liable for?** Credential storage, card data, PII, email
  deliverability. Buying moves that obligation to someone whose business is meeting it.

Prefer options that speak a **standard** (OIDC, SMTP, S3, OpenTelemetry, SQL) and put the
WRAP adapter on the standard, not on proprietary extensions.

### 4. TEST — terminal, or split?

**Split where the decision class stops being uniform.** If part of the node would be
bought and part built, that boundary *is* the seam — you cannot refactor across a
vendor's API, so it is already a real interface.

Terminal when:

| Because | Condition |
|---------|-----------|
| **Procured** | Uniformly BUY/ADOPT → spec the *seam*, never the vendor's internals |
| **Atomic build** | BUILD/WRAP implementable in one TDD session against one test seam |
| **Deferred** | DEFER → Type B ticket; subtree resumes when it closes |

Must decompose when parts resolve to **different** classes, or when uniformly BUILD but
too large for one session.

**Do not decompose past a procurement boundary.** Once identity verification resolves to a
managed IdP, you do not then spec OIDC, JWT signing, and RSA. That is the termination
guarantee — and subtree depth then honestly measures how much you are building.

### 5. SPECIFY

Terminal nodes get the full template below **including §8**. Non-terminal nodes get
§1–§5 plus a child index.

---

## Depth guards

1. **Max depth 4** (L0→L3) by default; deeper needs an ADR on the node.
2. **Procurement terminates.**
3. **Distinct failure mode:** a child that cannot fail independently of its siblings is a
   step in a procedure, not a component.
4. **Two-child minimum:** one child is a rename, not a decomposition — collapse it.
5. **No speculative children:** fog goes to the Wayfinder map, not into invented nodes.

Expect **shallow where the world has solved it, deep where you are actually building**. A
uniformly deep tree means RESEARCH is being skipped.

---

## Invariants — EARS + Epistemic Stage

Every invariant uses an EARS pattern and carries an evidence tag.

- **[Ubiquitous]** `The [System] SHALL [behavior]`
- **[Event-driven]** `WHEN [trigger] THE SYSTEM SHALL [behavior]`
- **[State-driven]** `WHILE [state] THE SYSTEM SHALL [behavior]`
- **[Conditional]** `IF [condition] THEN THE SYSTEM SHALL [behavior]`

| Stage | Meaning |
|-------|---------|
| `Unknown` | Asserted without inspection |
| `Observed` | Verified in syntax/AST |
| `Sampled` | Unit tests / mock probes — **never** promotable to Proved |
| `Inferred` | Structural pattern match |
| `Measured` | Hardware-benchmarked with variance (`measure.sh`) |
| `Proved` | Solver (Z3/SMT) or algebraic rule |
| `Refuted` | Contradicted by counterexample |

---

## Incomplete-work gate

Maintain **one** checklist: `docs/open-work.md` (`ready` | `blocked` | `deferred` |
`research` | `done`). Do not create parallel readiness or fog lists. Claimable build
tickets go to `.scratch/wayfinder-map/MAP.md`; DEFER nodes become Type B tickets there.

---

## `SYSTEM.md` template

```markdown
# [Component Name] (Level N)

## 1. System Intent & Responsibility
Single-sentence responsibility. Explicit non-goals ("does not own: ...").

## 2. Sub-System Decomposition
- **[Child](./child/SYSTEM.md)** — role and interface boundary.
<!-- Terminal nodes instead state: "Atomic leaf (procured | atomic build | deferred)." -->

## 3. Interface Contracts
- **Inputs:** types, events, configuration, state passed in.
- **Outputs:** returned data, events emitted, state mutations.

## 4. Invariants (EARS + Epistemic Stage)
- [Ubiquitous] The component SHALL ...
  - `EvidenceStage:` Observed | Sampled | Measured | Proved

## 5. Architectural Decisions (ADRs)
- **ADR-001:** [Title] — context, decision, impact.

## 6. Leaf Execution & Test Seam (terminal nodes only)
- **Implementation File(s):** relative path to source.
- **Test Surface Seam:** primary test file (`checks.sh` target).

## 7. Measurement Seams (terminal nodes only)
- **Primary Metric:** `[metric_name]` (target, and `direction: lower|higher`)
- **Harness Path:** `components/[name]/measure.sh`
- **Correctness Backpressure:** `components/[name]/checks.sh`
- **Telemetry Surface:** structured JSON for self-diagnostics
- **Branching Policy:** worktree hypothesis; merge only when checks pass AND the primary
  metric does not regress AND no telemetry contradiction

## 8. Technology Resolution (terminal nodes only)
- **Decision class:** BUY | ADOPT | WRAP | BUILD | DEFER
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
- **Open questions:** OW-nn / Wayfinder ticket, or "none"
```

`BUILD` nodes add a **Justification** line in §8 naming which of the five BUILD conditions
applies. A BUILD with no recorded justification is the failure this gate exists to catch.

---

## Finishing

1. Every terminal node has §6, §7, §8 complete.
2. Every DEFER has a Type B ticket on the Wayfinder map.
3. `docs/open-work.md` reflects process incompleteness (not one row per leaf).
4. Report the shape: node count, depth, and the **BUILD ratio** — how much of this you are
   actually writing. A high ratio early is the signal to re-run RESEARCH.
