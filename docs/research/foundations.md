# Research Foundations

This document records the external evidence behind Recurspec and the limits of that evidence. It is not a claim that the Recurspec workflow has already been validated as a whole.

## Evidence policy

- Cite original research, standards, or first-party technical material.
- State only what the cited source actually establishes. A case study is not a universal result; a standard is normative guidance, not an effectiveness experiment.
- Label a Recurspec-specific mechanism as a **design inference** when the source motivates it but does not evaluate that mechanism.
- Treat passing tests as evidence about the exercised cases, not proof of general correctness.
- Use `EvidenceStage: Unknown` for an uncited or unmeasured claim. Never manufacture a title, identifier, result, or citation.

## 1. Constrained natural-language requirements: EARS

Mavin, Wilkinson, Harwood, and Novak introduced the Easy Approach to Requirements Syntax (EARS) as a small set of templates that constrain, but do not replace, natural language. Their RE'09 paper reports a Rolls-Royce case study in which the authors applied EARS while extracting aero-engine control requirements and observed qualitative and quantitative improvements over the conventional text they studied. The five basic patterns in the paper are ubiquitous, event-driven, unwanted-behaviour, state-driven, and optional-feature requirements; patterns may be combined. See [Mavin et al., *Easy Approach to Requirements Syntax (EARS)*, IEEE RE 2009](https://doi.org/10.1109/RE.2009.9).

**What this supports:** using a consistent clause structure to expose several common defects in natural-language requirements, such as ambiguity, vagueness, and unnecessary complexity.

**What this does not support:** a universal claim that EARS eliminates ambiguity, prevents implementation drift, makes requirements complete, or proves temporal behaviour. The published evidence is a bounded industrial case study, and EARS remains natural language.

**Recurspec design inference:** behavioural invariants in `SYSTEM.md` should use the closest EARS pattern, with combined patterns only when needed. Each invariant should have a stable identifier and a separately defined verification seam. The mapping from an EARS sentence to a test or metric is a Recurspec convention, not a result established by the EARS paper. Mathematical constraints, decision tables, state machines, or temporal logic should be used when prose is the weaker representation.

## 2. Independent verification and maker-checker separation

NASA defines independent verification and validation (IV&V) as rigorous analysis and testing that produces objective evidence and an independent assessment across the software life cycle. Its standard distinguishes technical, managerial, and financial independence. Technical independence requires that IV&V personnel not be involved in development; managerial independence includes control over analysis scope, methods, and schedule; financial independence protects the work from development-budget pressure. See section 4.4 of [NASA-STD-8739.8B, *Software Assurance and Software Safety Standard*](https://standards.nasa.gov/sites/default/files/standards/NASA/B/0/NASA-STD-87398RevB.pdf). IEEE also defines lifecycle V&V processes in [IEEE 1012-2024, *Standard for System, Software, and Hardware Verification and Validation*](https://standards.ieee.org/ieee/1012/7324/).

**What this supports:** an assessor needs sufficient separation to form an independent technical view and to report adverse findings without the developer controlling the evaluation.

**What this does not support:** a general empirical claim that two AI agents always outperform one, or that merely assigning different role names creates independence. Agents that share a model, training data, prompt context, or tools may have correlated failures. Recurspec usually cannot reproduce NASA's organizational and financial independence.

**Recurspec design inference:** the actor that proposes a production change must not be the sole authority that accepts it. The checker should own the acceptance criteria, run evidence-producing checks from a clean state, and be able to reject the change without editing the criteria to accommodate it. This is an engineering analogue of technical and managerial independence, not formal IV&V certification. For low-risk changes, automation may be the checker; higher-risk changes need proportionally stronger independent review.

## 3. Iterative generation, feedback, and repair

The original spiral model is a broader software-process precedent for iterative, risk-driven development. Each cycle identifies objectives, alternatives, and constraints; evaluates alternatives and resolves risk; develops and verifies the next-level product; and plans the next cycle. Boehm presents a process model, not a theorem that iteration converges or improves every project. See [Boehm, *A Spiral Model of Software Development and Enhancement*, 1988](https://doi.org/10.1109/2.59).

Generate-and-validate program repair is a concrete precedent for an iterative candidate-evaluation loop. Weimer et al. used genetic programming to create program variants, standard test cases to encode required behaviour, and minimization after a successful candidate was found. Their initial experiments covered ten C programs, so the result demonstrates feasibility in that setting rather than a general repair guarantee. See [Weimer et al., *Automatically Finding Patches Using Genetic Programming*, ICSE 2009](https://doi.org/10.1109/ICSE.2009.5070536).

Subsequent primary evidence shows why the evaluator cannot be treated as an oracle for full correctness. Qi et al. re-analysed patches from generate-and-validate systems and found both validation-infrastructure errors and many patches that satisfied weak test proxies while deleting desirable functionality or introducing vulnerabilities. See [Qi et al., *An Analysis of Patch Plausibility and Correctness for Generate-and-Validate Patch Generation Systems*, ISSTA 2015](https://doi.org/10.1145/2771783.2771791). NASA likewise recommends beginning IV&V early so evidence can feed back into development while changes are still timely; this is lifecycle guidance, not a proof of any particular repair algorithm ([NASA-STD-8739.8B, section 4.4](https://standards.nasa.gov/sites/default/files/standards/NASA/B/0/NASA-STD-87398RevB.pdf)).

**What this supports:** candidate generation, evaluation, feedback, and another attempt can be operationalized; the validity of the loop is bounded by the quality of its specifications, tests, instrumentation, and acceptance rule.

**Recurspec design inference:** evaluate a change in isolation, preserve the pre-change result as a comparator, run correctness checks before optimization metrics, and keep the candidate only when the declared acceptance rule is met. A failing candidate should produce a diagnostic packet for the next attempt. A passing candidate is **accepted under the current evidence**, not proved correct. Repeated repair without new information should terminate or escalate rather than loop indefinitely.

## 4. Architecture decision records

Michael Nygard's original ADR article proposes short, repository-local records for architecturally significant decisions. Its template records title, context, decision, status, and consequences; superseded decisions remain in the history and point to their replacements. See [Nygard, *Documenting Architecture Decisions* (2011)](https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions).

**What this supports:** a lightweight, version-controlled format for preserving the motivation and consequences of significant decisions. The source is a first-party practitioner proposal with a small experience report, not a controlled study proving maintainability or productivity gains.

**Recurspec design inference:** a `SYSTEM.md` node may embed an ADR-shaped decision block when the decision is local to that node. It should preserve context, alternatives considered, decision, status, consequences, and a supersession link. Recurspec's epistemic stages, falsification triggers, and measurement seams extend the original ADR format and must not be attributed to Nygard.

## 5. Software measurement and baselines

[ISO/IEC/IEEE 15939:2017](https://www.iso.org/standard/71197.html) defines a software and systems measurement process that begins with information needs, selects and defines measures, applies analysis results, and determines whether those results are valid. The standard supplies a process framework; it does not select Recurspec's metrics or acceptance thresholds.

NIST warns that software performance results can be plausible but wrong because of small samples, invalid statistical assumptions, instrumentation faults, uncontrolled system state, and unrepresentative workloads. It calls for reproducible reporting, representative workloads, attention to random and systematic error, and appropriate uncertainty analysis. See [Pieterse and Flater, *The Ghost in the Machine*, NIST TN 1830 (2014)](https://doi.org/10.6028/NIST.TN.1830). NIST further cautions that many software metrics are simple counts used as indicators for more abstract qualities, rather than direct measurements of those qualities; see [Flater et al., *A Rational Foundation for Software Metrology*, NISTIR 8101 (2016)](https://doi.org/10.6028/NIST.IR.8101).

[ISO/IEC 25010:2023](https://www.iso.org/standard/78176.html) supplies a product-quality reference model with nine characteristics and associated subcharacteristics. It can help identify what should be specified and evaluated, but it does not prescribe a single scalar quality score or establish project-specific weights.

**Recurspec design inference:** every optimization claim should identify:

- the decision-relevant information need;
- the measurand, unit, workload or fixture, collection procedure, and tool versions;
- the pre-change baseline and candidate result under comparable conditions;
- repeated observations or an uncertainty treatment when noise can change the decision;
- a direction, threshold, and stopping rule declared before observing the candidate; and
- retained raw observations sufficient to audit the conclusion.

A baseline is a versioned comparator, not timeless ground truth. If environment, workload, instrumentation, or measurement method changes materially, establish a new baseline and record the break in comparability. One measurement run supports only a claim about that run unless variability is known to be negligible.

## 6. Multiple verification techniques and evidence levels

NIST recommends a portfolio of developer-verification techniques, including automated testing, static scanning, structural and black-box tests, historical cases, fuzzing, and review of included components. NIST explicitly says that this portfolio does not cover the totality of software verification. See [Black, Guttman, and Okun, *Guidelines on Minimum Standards for Developer Verification of Software*, NISTIR 8397 (2021)](https://doi.org/10.6028/NIST.IR.8397).

**What this supports:** different techniques expose different classes of defects, so one green signal should not stand in for all assurance evidence.

**Recurspec design inference:** classify evidence by what it actually observes:

| Evidence class | Examples | Bounded conclusion |
| --- | --- | --- |
| Executed behaviour | unit, integration, property, fuzz, and regression tests | The observed cases satisfied their oracles in the recorded environment. |
| Static structure | parser, type checker, linter, AST or schema policy | The inspected artifact satisfied those rules. |
| Empirical quality | latency, throughput, memory, accuracy, failure rate | The measured workload produced the reported distribution or estimate. |
| Model judgement | rubric-based model review | The named model and rubric produced an advisory assessment. |
| Human decision | risk acceptance, product judgement, exception approval | An accountable person accepted the recorded evidence and residual risk. |

These classes are not a universal hierarchy, and a higher row does not subsume another. The required combination should follow the risk and the claim being made. A model judgement should not be the only gate for a deterministic invariant that can be checked directly.

## 7. Composite quality is an unvalidated control hypothesis

Recurspec may use a weighted geometric aggregate as an internal control surface:

\[
Q(S)=\exp\left(\sum_i w_i\ln q_i(S)\right),
\qquad q_i\in(0,1],\quad w_i\geq 0,\quad \sum_i w_i=1.
\]

ISO/IEC 25010 can inform the vocabulary of product-quality dimensions, but it does **not** validate this equation, the selected dimensions, their normalization, their independence, or their weights. The aggregate can also hide compensating changes and measurement uncertainty.

Therefore `Q(S)` is `EvidenceStage: Unknown` until Recurspec defines each component operationally, publishes the weights and missing-data rule, tests sensitivity to normalization and weights, and validates whether changes in the score predict outcomes users actually value. Hard safety or correctness constraints must remain non-compensatory gates rather than dimensions that a high score elsewhere can offset.

## 8. Claim boundary for Recurspec

The sources above justify individual design ingredients. They do not establish that Recurspec as an integrated method improves defect rate, delivery time, architecture quality, agent reliability, or cost. Those are empirical hypotheses for this project.

Any future effectiveness claim should pre-register at least the task population, comparator workflow, outcome measures, failure definition, stopping rule, sample size rationale, analysis method, and treatment of retries and human intervention. Report null and adverse results, not only successful demonstrations. Until comparative evaluation exists, describe Recurspec as a **research-informed workflow**, not a research-validated one.

## Primary-source bibliography

1. Mavin, A., Wilkinson, P., Harwood, A., & Novak, M. (2009). [*Easy Approach to Requirements Syntax (EARS)*](https://doi.org/10.1109/RE.2009.9). 17th IEEE International Requirements Engineering Conference, 317-322.
2. NASA (2022). [*NASA-STD-8739.8B: Software Assurance and Software Safety Standard*](https://standards.nasa.gov/sites/default/files/standards/NASA/B/0/NASA-STD-87398RevB.pdf), section 4.4.
3. IEEE (2024). [*IEEE 1012-2024: Standard for System, Software, and Hardware Verification and Validation*](https://standards.ieee.org/ieee/1012/7324/).
4. Boehm, B. W. (1988). [*A Spiral Model of Software Development and Enhancement*](https://doi.org/10.1109/2.59). *Computer*, 21(5), 61-72.
5. Weimer, W., Nguyen, T., Le Goues, C., & Forrest, S. (2009). [*Automatically Finding Patches Using Genetic Programming*](https://doi.org/10.1109/ICSE.2009.5070536). ICSE 2009.
6. Qi, Z., Long, F., Achour, S., & Rinard, M. (2015). [*An Analysis of Patch Plausibility and Correctness for Generate-and-Validate Patch Generation Systems*](https://doi.org/10.1145/2771783.2771791). ISSTA 2015.
7. Nygard, M. (2011). [*Documenting Architecture Decisions*](https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions).
8. ISO/IEC/IEEE (2017). [*15939:2017 Systems and software engineering — Measurement process*](https://www.iso.org/standard/71197.html).
9. Pieterse, V., & Flater, D. W. (2014). [*The Ghost in the Machine: Don't Let It Haunt Your Software Performance Measurements*](https://doi.org/10.6028/NIST.TN.1830). NIST Technical Note 1830.
10. Flater, D. W., Black, P. E., Fong, E. N., Kacker, R. N., Okun, V., Wood, S. S., & Kuhn, D. R. (2016). [*A Rational Foundation for Software Metrology*](https://doi.org/10.6028/NIST.IR.8101). NISTIR 8101.
11. ISO/IEC (2023). [*25010:2023 Systems and software Quality Requirements and Evaluation — Product quality model*](https://www.iso.org/standard/78176.html).
12. Black, P., Guttman, B., & Okun, V. (2021). [*Guidelines on Minimum Standards for Developer Verification of Software*](https://doi.org/10.6028/NIST.IR.8397). NISTIR 8397.
