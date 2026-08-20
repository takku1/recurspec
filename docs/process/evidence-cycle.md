# Evidence cycle

Recurspec advances a project through one internal control law:

```text
DISCOVER -> RESOLVE -> EXECUTE -> CHECK -> RECONCILE -> repeat
```

This is evidence-driven adaptive planning: select the smallest coherent transition,
learn from it, and replan. It borrows Agile's preference for feedback without requiring
a framework, ceremony, role, calendar sprint, or fixed batch size. A cycle ends when its
question has enough evidence to route safely.

## Operations

| Operation | Question | Result |
|---|---|---|
| Discover | What capability, gap, interface, or uncertainty matters now? | Contract or reviewable proposal |
| Resolve | Is the next seam `BUY`, `ADOPT`, `WRAP`, `BUILD`, or `DEFER`? | Technology Resolution or Research Frontier |
| Execute | What is the next bounded, independently failing change? | Isolated Candidate |
| Check | What do deterministic checks and measurements establish? | Typed findings and Candidate evidence |
| Reconcile | Which representation must change: code, contract, assumption, instrument, or work order? | Reviewable draft and updated route |

Recursive specification is lazy. Coarse future branches remain coarse until a decision
needs them; a `BUILD` or `WRAP` branch decomposes only to one-session Atomic Leaves.
`BUY` and `ADOPT` terminate at the Procurement Seam. Cheap experiments may resolve an
uncertainty sooner than speculative architecture prose, but their measurements apply
only to their stated workload and environment.

## Authority

The Architect owns contracts, handoffs, final decisions, and reconciliation. The
Implementor owns source and tests on an isolated Candidate. A different checker executes
the trusted gate and supplies typed approval bound to the exact Candidate commit.

```text
Contract Tree + ROADMAP
          |
          v
   bounded handoff
          |
          v
isolated Candidate -- maker
          |
          v
checks + measures -- checker
          |
    +-----+------+
    |            |
 KEEP/REVERT   ESCALATE
    |            |
    +------> reconcile -> status
```

`NEED_CHECKER` is a routing state, not a fourth Evaluation Gate outcome. Instrument
failure is also not an outcome; ambiguous, malformed, contradictory, or missing evidence
returns an error.

## Evidence licenses

| Evidence class | Licenses | Does not license |
|---|---|---|
| Executed behavior | Exercised cases satisfied their oracles | General correctness or product outcome |
| Static structure | Inspected artifacts satisfied the named rules | Runtime behavior |
| Empirical measurement | This workload in this environment | Another workload or scale |
| Model judgment | The named model and rubric produced a proposal | Ground truth or merge authority |
| Human decision | An accountable person accepted residual risk | Proof that the decision was correct |

Passing tests are `Sampled`; runtime measurements are `Measured`; only formal proof is
`Proved`. A common Finding envelope preserves these distinctions—it does not flatten
them.

## Candidate evaluation

Each measurable Atomic Leaf names `modules/<name>/checks.sh` and `measure.sh` in §7.
Checks must pass before metrics are considered. Metrics use one of four tiers:

| Tier | Rule |
|---|---|
| `hard_gate` | Unknown or regression blocks |
| `target` / `optimization` | Regression beyond tolerance blocks; neutral keeps |
| `observation` | Record only; never blocks |

The gate evaluates with baseline-owned probes and trusted inputs in a disposable
worktree. Every `REVERT` records a Negative Pattern. Five consecutive or eight total
reverts on one Candidate branch escalate. `KEEP` may fast-forward the verified baseline
branch, but Best Known State promotion is a separate explicit post-merge evaluation.

## Replanning

After each accepted, reverted, or deferred transition, run `recurspec status` again.
Reconciliation may delete future work when evidence proves it unnecessary; it must not
only add tasks. `ROADMAP.md` remains the sole authority for incomplete intent, while job
state, handoffs, Research Frontier tickets, and relationship indexes remain regenerable
views.

The system stops at `PASS`, `DEFER`, `ESCALATE`, `NEED_CHECKER`, or a decision requiring
the user. Until R-400–R-403 produce outcome data, Recurspec is research-informed rather
than research-validated.
