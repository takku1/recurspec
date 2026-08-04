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
