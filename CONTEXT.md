# Recurspec

Recurspec describes how a software goal becomes a finite, evidence-backed design and how
implementation feedback changes that design without erasing intent.

## Language

**Contract Tree**:
A hierarchy of design contracts rooted in one system goal and divided at independently
failing seams.
_Avoid_: Spec tree, fractal tree, blueprint

**Contract Node**:
One responsibility in the Contract Tree with explicit intent, interface, invariants, and
evidence maturity.
_Avoid_: Component, subsystem

**Atomic Leaf**:
A terminal Contract Node that is either procured, deferred, or implementable in one
test-driven session through one seam.
_Avoid_: Task, work item

**Decision Class**:
Exactly one resolution assigned before decomposition: `BUY`, `ADOPT`, `WRAP`, `BUILD`, or
`DEFER`.
_Avoid_: Build-versus-buy status

**Procurement Seam**:
The terminal interface where a `BUY` or `ADOPT` decision meets behavior owned by the
system.
_Avoid_: Vendor internals, procurement boundary

**Fit Gap**:
Required behavior that a selected dependency does not provide and that therefore remains
inside the system's ownership.
_Avoid_: Missing feature

**Candidate**:
An isolated proposed change evaluated before it can alter the accepted system state.
_Avoid_: Hypothesis, patch

**Evaluation Gate**:
The decision module that combines correctness checks, metric comparison, telemetry
honesty, and bounded retries into `KEEP`, `REVERT`, or `ESCALATE`.
_Avoid_: Harness, runner

**Best Known State**:
The explicitly promoted reference metric vector against which later Candidates are
evaluated.
_Avoid_: Latest result, automatic baseline

**Negative Pattern**:
Evidence recorded for a reverted Candidate so a later repair does not repeat an
invalidated approach.
_Avoid_: Error log

**Structural Feedback**:
Evidence that implementation shape and the Contract Tree disagree.
_Avoid_: Back-Channel A

**Empirical Feedback**:
Evidence that measured behavior and a Contract Node's claims disagree.
_Avoid_: Back-Channel B

**Evidence Stage**:
The maturity of a claim: `Unknown`, `Observed`, `Sampled`, `Inferred`, `Measured`,
`Proved`, or `Refuted`.
_Avoid_: Confidence level

**Research Frontier**:
An uncertainty that must be resolved before a Contract Node can be completed.
_Avoid_: Type B ticket, fog
