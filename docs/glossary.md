# Ubiquitous Language Glossary

Canonical domain terms for RSS. Use these words consistently in specs, skills, ADRs, and agent prompts.

---

## Spec tree

| Term | Definition |
|------|------------|
| **L0 Root Spec** | Top-level architecture contract: `docs/architecture/SYSTEM.md`. Global intent, decomposition index, root invariants. |
| **Sub-System (L1..LN)** | A node in the fractal tree for an isolated domain with its own interfaces. |
| **Atomic Leaf Node** | Bottom-level node implementable in one TDD session. Must include §6 Test Seam and §7 Measurement Seams. |
| **EARS Notation** | Easy Approach to Requirements Syntax: `[Ubiquitous]`, `[Event-driven]`, `[State-driven]`, `[Conditional]` (Mavin et al., RE'09). |
| **Epistemic Stage** | Evidence maturity of an invariant: `Unknown`, `Observed`, `Sampled`, `Inferred`, `Measured`, `Proved`, `Refuted`. **Sampled** (unit tests) must not be promoted to **Proved** without formal proof or measured evidence. |

---

## Decomposition & technology resolution

Process: [decomposition-loop](./process/decomposition-loop.md) · [technology-resolution](./process/technology-resolution.md)

| Term | Definition |
|------|------------|
| **Decision Class** | The resolution assigned to every node before it is decomposed or specified: `BUY` (managed third-party service), `ADOPT` (OSS library or framework feature you run), `WRAP` (thin adapter of your own over a BUY/ADOPT), `BUILD` (genuinely custom), `DEFER` (unresolved → Type B ticket). |
| **Resolution Gate** | The point where a node's decision class is fixed. Resolution *precedes* decomposition: a node is asked *what will implement this?* before *what are its parts?* |
| **Procurement Boundary** | A node resolved BUY or ADOPT. Terminal by definition — the vendor owns the internals, so the spec describes the **seam**, never the vendor's implementation. The primary termination condition of recursion. |
| **Uniform Resolution Test** | The splitting rule: decompose when a node's parts would resolve to *different* decision classes, splitting on that fault line. A procurement boundary is already a real interface — you cannot refactor across a vendor's API. |
| **Atomic Build** | A terminal node resolved BUILD or WRAP that one engineer or agent can implement in a single TDD session against a single test seam. The second termination condition. |
| **Fit Gap** | What a selected BUY/ADOPT option does *not* cover. Recorded in §8; it is the source of the node's sibling children. |
| **Exit Cost** | `LOW \| MEDIUM \| HIGH` — what swapping a procured dependency would actually require. Lowered by preferring standard protocols and confining vendor types to the WRAP adapter. |
| **Seam Standard** | The interop protocol (OIDC, SMTP, S3, OpenTelemetry, SQL) a WRAP adapter is written against instead of a vendor's proprietary extensions. What keeps Exit Cost LOW. |
| **BUILD Ratio** | Share of terminal nodes classed BUILD — how much of the system you are actually writing. A high ratio early signals the RESEARCH phase is being skipped. |
| **§8 Technology Resolution** | The block on every terminal node recording decision class, selected product and pin, alternatives with rejection reasons, fit gap, seam, exit cost, cost model, liability transferred, operational owner, and failure mode. Replaces the two-line topic summary of a flat plan. |

---

## Dual back-channels

| Term | Definition |
|------|------------|
| **Back-Channel A (Structural)** | Code/AST shape → blueprint. Drift, bloat, test seams. Skills: `/reconcile-spec`, AST gatekeeper. *Does the blueprint describe what exists?* |
| **Back-Channel B (Empirical)** | Measured behavior → blueprint. Metric drift, invariant violation, telemetry contradiction. Skills: measure harness, `/graybox`, `/sherloc`. *Does the blueprint describe how it behaves?* |
| **SDB Gate** | Stochastic–Deterministic Boundary: LLM proposals pass deterministic filters (AST, schema, tests, baselines) before commit (Thompson 2025; SDB methodology 2026). |

---

## Execution & measurement

| Term | Definition |
|------|------------|
| **Strategy Packet** | Bounded Outer-Loop instruction set for the Inner Implementor. |
| **Correction Packet** | Repair instruction when Inner output fails Outer verification. |
| **Correctness Backpressure (`checks.sh`)** | Mandatory suite that must pass before metric-based keep is allowed. |
| **Measurement Harness (`measure.sh`)** | Captures latency/throughput/accuracy with variance; feeds Back-Channel B. |
| **Hypothesis Branch** | Isolated worktree: create → mutate → measure → keep \| revert. |
| **Metric Drift (Signal D)** | Performance regression beyond tolerance; triggers research ticket and optional Sherloc pivot. |

---

## Frontier & decisions

| Term | Definition |
|------|------------|
| **Wayfinder Map** | Shared frontier index: `.scratch/wayfinder-map/MAP.md`. |
| **Type A Frontier** | Contract known; ready for implementation. |
| **Type B Frontier** | Boundary unknown; needs `/research` or `/prototype` before locking spec. |
| **Open Work** | Single incomplete-work registry: `docs/open-work.md` (not parallel checklists). |
| **Ratchet Metric** | Session compounding: each tool/spec should reduce cost and increase reach of later work. |
