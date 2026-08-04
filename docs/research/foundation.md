# Research Foundation

PhD-grade grounding for RSS. **Only citable sources.** Placeholder arXiv IDs and invented titles are prohibited. When a claim lacks a primary source, state `EvidenceStage: Unknown` in the relevant `SYSTEM.md` rather than fabricating a reference.

---

## 1. Constrained natural-language requirements (EARS)

**Claim:** Unconstrained prose requirements cause implementation drift under multi-agent coding; lightly constrained patterns improve precision without formal methods overhead.

| Item | Citation |
|------|----------|
| Primary | Mavin, A., Wilkinson, P., Harwood, A., & Novak, M. (2009). *Easy Approach to Requirements Syntax (EARS)*. 17th IEEE International Requirements Engineering Conference (RE'09). |
| Overview | [alistairmavin.com/ears](https://alistairmavin.com/ears/); Wikipedia: Easy Approach to Requirements Syntax |

**RSS use:** All invariants in `SYSTEM.md` use EARS patterns: Ubiquitous, Event-driven, State-driven, Conditional (and Unwanted where needed). Atomic leaves map EARS clauses to tests (`checks.sh`) and, where relevant, metrics (`measure.sh`).

**Epistemic caution:** EARS improves *clarity* of requirements. It does not by itself prove temporal properties. Mapping EARS → temporal logic is a research direction (treat as design intent, not established theorem, unless formally encoded).

---

## 2. Stochastic–deterministic boundary (SDB)

**Claim:** LLM agents are stochastic; production software requires deterministic guarantees. Reliability requires an explicit boundary: propose (stochastic) → verify (deterministic) → commit/reject.

| Item | Citation |
|------|----------|
| Dual-state execution | Thompson, M. (2025). *The Dual-State Architecture for Reliable LLM Agents*. arXiv:2512.20660. DSAP: couple generation with deterministic post-condition verification; dual-state \(S_{\text{workflow}}\) vs \(S_{\text{env}}\). |
| SDB as first-class contract | Srinivasan, V. et al. (2026). *A Methodology for Selecting and Composing Runtime Architecture Patterns for Production LLM Agents*. arXiv:2605.20173. Names the **stochastic-deterministic boundary (SDB)** as proposer + verifier + commit + reject. |

**RSS use:** The SDB Gate sits after Outer Loop measurement and AST checks. Implementor self-tests are non-authoritative. Maker ≠ checker.

---

## 3. Multi-agent role separation (anti-authority drift)

**Claim:** Single agents that write contracts, implement, and self-grade tend to weaken contracts to make tests pass (“authority drift”). Separation of planner / implementor / verifier reduces that failure mode.

| Item | Citation |
|------|----------|
| Runtime architecture patterns | arXiv:2605.20173 (above) — verifier and reject signal as architectural objects. |
| Dual-state recovery limits | arXiv:2512.20660 — execution recovery is necessary but not sufficient for end-to-end autonomous SE; plan synthesis remains hard. |
| Requirements with symbolic validation | *Model-Driven Requirements Configuration with Three-Valued Scoring* style neuro-symbolic pipelines (e.g. arXiv:2607.26220) — LLM proposes; deterministic validator enforces structural constraints. |

**RSS roles:**

| Role | Responsibility | Must not |
|------|----------------|----------|
| Architect | Spec tree, EARS, Wayfinder Type B research | Implement production code in the same turn as contract lock without audit |
| Implementor | TDD against leaf §4/§6; strategy packet only | Edit parent contracts; own merge decision |
| Auditor | checks/measure/graybox/AST; blueprint updates via back-channels | Grade work it authored |

---

## 4. Branching measurement (edit → measure → keep|revert)

**Claim:** Agentic optimization without isolated hypothesis branches conflates experiments; workflows need explicit branch lifecycle and evaluation.

| Item | Citation |
|------|----------|
| Agentic branching workloads | Ang, E. et al. (2026). BranchBench — *Aligning Database Branching with Agentic Demands* / extensible agentic branching benchmark. arXiv:2604.17180. Branch–mutate–evaluate–prune topology. |
| Autoresearch pattern | Karpathy et al., [autoresearch](https://github.com/karpathy/autoresearch) (and community forks such as amp-autoresearch): edit → measure → keep/revert on isolated experiments. |
| Observability-driven development | Industry ODD practice: design measurement seams when designing interfaces (not only after green tests). |

**RSS use:** Hypothesis worktrees; `checks.sh` as correctness backpressure; `measure.sh` for primary metrics; keep only if checks pass **and** metric improves **and** telemetry is non-contradictory.

---

## 5. Verification ladder (do not confuse levels)

**Claim:** “Tests pass” is not the same class of evidence as schema/AST policy, delayed integration truth, model-judge rubrics, or human approval.

| Level | Check type | RSS mechanism | Merge authority |
|-------|------------|---------------|-----------------|
| L1 Deterministic | Exit code, assertion, golden | `checks.sh`, unit tests, EARS→test | Required |
| L2 Rule/schema | Linter, AST, policy | AST Gatekeeper, EARS syntax validation | Required for contract-touching changes |
| L3 Delayed truth | Integration, realistic load | `measure.sh`, graybox fixtures | Required for performance-sensitive leaves |
| L4 Model judge | Rubric / LLM score | Optional advisory only | **Not** a merge gate |
| L5 Human | Manual | Wayfinder HITL tickets | As ticket type requires |

Sources informing this ladder include dual-state / SDB literature (above) and gray-box evaluation practice (instrument telemetry is a *claim*, not ground truth — see local `/graybox` skill).

---

## 6. Living documentation / multi-signal feedback

**Claim:** Static docs diverge under rapid agent edits. Feedback from code structure (AST coverage of specs), size/complexity thresholds, and test-introduced seams keeps the blueprint aligned.

| Item | Citation / basis |
|------|------------------|
| Requirements traceability | Classical RE practice: maintain links between requirements and design/code (IEEE requirements engineering body of work; EARS as lightweight syntax layer). |
| Architectural decision records | Nygard, M. *Documenting Architecture Decisions* (ADR pattern) — context/decision/consequences; RSS inlines lightweight ADRs in each `SYSTEM.md`. |
| Spec-driven agent workflows | Emerging SDD tooling patterns (e.g. Kiro / Spec-Kit class tools) — treat specs as first-class artifacts in the agent loop (engineering practice; cite product docs when claiming specific tool behavior). |

**RSS signals (structural, Back-Channel A):** code drift, line/responsibility bloat, test-seam expansion. **Empirical (Back-Channel B):** invariant violation under measure, performance regression, telemetry contradiction, unknown boundary → Type B ticket.

---

## 7. Cumulative quality (design intent)

**Claim:** Optimizing a single dimension (test pass rate) can collapse documentation, architecture, or epistemic honesty. A multiplicative / geometric aggregation penalizes near-zero dimensions.

RSS **design intent** (not yet an empirically validated published model for this repo):

\[
Q(S) = \exp\left(\sum_i w_i \ln q_i(S)\right)
\]

with dimensions such as architecture fidelity, implementation correctness, epistemic honesty, performance, complexity control, documentation sync, and ratchet. Treat \(Q(S)\) as an internal control surface (`EvidenceStage: Unknown` until instrumented). See open work OW-14.

---

## How to expand research in component docs

When deepening a subsystem `SYSTEM.md`:

1. State the **engineering claim** in one sentence.
2. Attach **primary sources** from this file or add a new row here first.
3. Tag invariants with Epistemic Stages; do not claim Proved from Sampled tests.
4. Prefer recursive *interface* decomposition over essay-length prose in architecture nodes; keep long arguments in `process/` or `research/`.
