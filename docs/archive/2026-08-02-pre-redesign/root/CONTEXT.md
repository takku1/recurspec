# Recursive System Specification (RSS) — Ubiquitous Language Glossary

This document serves as the canonical domain glossary for RSS. Use these terms precisely in all specifications, agent prompts, and ADRs.

---

## Architecture & Spec Tree Concepts

- **L0 Root Spec:** Top-level architecture specification (`docs/architecture/SYSTEM.md`) defining global intent, root decomposition, and core invariants.
- **Sub-System (L1..LN):** A node in the spec tree representing an isolated architectural domain.
- **Atomic Leaf Node:** A bottom-level spec node that cannot be further divided. Implementable in a single TDD session and accompanied by Section 6 (Test Seam) and Section 7 (Measurement Seams).
- **EARS Notation:** Easy Approach to Requirements Syntax (`[Ubiquitous]`, `[Event-driven]`, `[State-driven]`, `[Conditional]`).
- **Epistemic Stage:** The evidence stage of a spec invariant (`Unknown`, `Observed`, `Sampled`, `Inferred`, `Measured`, `Proved`, `Refuted`). Sampled evidence (passing unit tests) must never be promoted to Proved without formal proof or hardware-measured benchmarks.

---

## Dual Back-Channel Concepts

- **Back-Channel A (Structural Reconciliation):** Sensory pipeline scanning code drift, spec bloat, and test seams (`/reconcile-spec`, AST Gatekeeper, `graphgraph`, `code-review-graph`). Answers: *"Does the blueprint describe what exists?"*
- **Back-Channel B (Empirical Reconciliation):** Sensory pipeline measuring component behavior, metric drift, and telemetry consistency (`measure.sh`, `checks.sh`, Sherloc audit). Answers: *"Does the blueprint describe how it actually behaves?"*
- **Stochastic-Deterministic Boundary (SDB Gate):** The verification boundary between stochastic LLM proposal and deterministic verification (AST check, test harness, baseline comparison).

---

## Execution & Measurement Harness Concepts

- **Strategy Packet:** The bounded instruction document produced by the Outer Loop Architect for the Inner Loop Implementor.
- **Correction Packet:** The repair instruction document issued when an Inner Loop execution fails Outer Loop verification.
- **Correctness Backpressure (`checks.sh`):** Mandatory test suite that MUST pass before any metric improvement is authorized for merge.
- **Measurement Harness (`measure.sh`):** Benchmark script capturing component latency, throughput, or accuracy with variance tracking.
- **Hypothesis Branch:** An isolated git worktree created for testing an edit/optimization hypothesis (`create → mutate → measure → keep/revert`).
- **Metric Drift (Signal D):** Performance regression exceeding tolerance (>20%), triggering automatic Sherloc `Serendipity` pivot and Wayfinder Type B ticket emission.

---

## Frontier & Decision Mapping

- **Wayfinder Map:** Shared frontier tracker index (`.scratch/wayfinder-map/MAP.md`).
- **Type A Frontier:** A ticket where the architectural contract is known and ready for implementation.
- **Type B Frontier:** A ticket where the architectural boundary or behavior is unknown, requiring `/research` or `/prototype` before locking spec.
- **Ratchet Metric:** Measurement of session-level compounding — whether each built tool/spec reduces the cost and increases the reach of subsequent discoveries.
