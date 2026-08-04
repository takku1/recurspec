---
name: sherloc
description: A formal system for bounded empirical derivation and logical auditing. Use for root-cause analysis, verification of complex system claims, or formal reasoning audits where cognitive bias and hypothesis-locking must be minimized.
---

# Sherloc Formal Reasoning System

Apply the `/sherloc` method to decompose a proposition, system, or argument into a dependency-aware proof ledger. This system mitigates hypothesis-locking by initializing a primary model, maintaining competing alternative models, applying adversarial verification, and executing evidence-driven `Serendipity` pivots when empirical data invalidates prior dependencies.

## 1. Operating Mode Selection

Evaluate the investigation using the Mode Selection Rubric to determine the required level of rigor.

**Mode Selection Rubric:**
Quantify each parameter (1-5):
1. Reversibility risk
2. Safety / harm risk
3. Organizational exposure
4. Evidence volatility
5. Strategic/Adversarial interference
6. System complexity

**Mode Thresholds:**
- **6-12 -> `compact`:** Minimal ledger for low-impact, reversible investigations with low evidence volatility.
- **13-21 -> `standard`:** Default system for dependency-aware investigation. Includes alternative models, contradiction tracking, and evidence-driven `Serendipity` pivots.
- **22+ (or any single parameter at 5) -> `full`:** Maximum rigor for high-impact, public, or safety-critical systems.

## 2. Core Structure Initialization

Initialize the response using this formal structure:

```text
Proposition: [The claim or question]
Mode: [compact | standard | full]
Decision target: [Objective function]
Evidence standard: [Required rigor level]
Depth target: [Recursive depth limit]

Initial model: [Primary hypothesis]
Alternative models: [Competing hypotheses]
Unknowns: [Unresolved variables]
Dependency graph: [Required for standard/full: Mermaid.js flowchart TD mapping Claim IDs and Status]

Proof ledger:
[Ledger entries]

Conclusion: [Summary of findings]
Remaining uncertainty: [Quantified or qualitative entropy]
Failure modes: [Logical or empirical vulnerabilities]
Disconfirming evidence: [Falsification conditions]
Next action: [Required follow-up]
```

## 3. Proof Ledger Maintenance

Construct the `Proof ledger` using this atomic line structure. Maintain strict separation between observation (raw data) and inference (interpretation).

```text
N. Claim: [Atomic sub-claim]
   Claim id: [Unique identifier]
   Depends on: [Prerequisite Claim IDs]
   Supports model(s): [IDs of strengthened models]
   Weakens model(s): [IDs of weakened models]
   Depth: [Integer: 0=root, 1=direct evidence, n=recursive obligation]
   Basis: [Rational basis for claim]
   Test / inspection: [Verification protocol]
   Execution command: [Literal shell command/script for technical evidence, or "N/A"]
   Cost: [very low | low | medium | high | very high]
   Evidence type: [mathematical proof | calculation | experiment | observation | source citation | simulation | static analysis | benchmark | trace | expert testimony | assumption]
   Evidence stage: [Unknown | Observed | Sampled | Inferred | Measured | Proved | Refuted]
   Confidence method: [qualitative judgment | calibrated probability | Bayesian update | likelihood ratio | benchmark outcome | mathematical proof | assumption]
   Observation: [Raw empirical data]
   Inference: [Logical interpretation of data]
   Status: [Open | Pending | Supports | Contradicts | Falsified | Inconclusive | Assumption | Quarantined | Established | Serendipity]
   Confidence before: [Prior value]
   Confidence after: [Posterior value]
```

## 4. Execution Mandates

1. **Iterative Derivation:** Do not proceed to a conclusion without populating the ledger.
2. **Dependency Propagation:** If a prerequisite claim status changes to `Falsified` or `Contradicts`, update all dependent claims to `Quarantined` or `Open`.
3. **Paraconsistent Quarantine:** Localize contradictions. Mark dependency-tainted claims as `Quarantined` and continue reasoning in unaffected logical regions.
4. **Serendipity Pivot:** Execute `Serendipity` when an alternative model achieves superior support, a core dependency is invalidated, or a hidden variable is identified.
5. **Epistemological Distinction:** Differentiate between internal coherence (logical consistency) and external correspondence (empirical matching). Sampled evidence must never be promoted directly to Proved without formal proof or hardware-measured benchmarks.
