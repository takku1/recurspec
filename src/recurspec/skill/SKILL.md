---
name: recurspec
description: Design and improve software through recursive contracts, technology resolution, isolated implementation, evidence evaluation, and reconciliation. Use with a raw goal, contract node, implementation ticket, failed candidate, or completed change.
---

# Recurspec

Advance a system by one evidence-backed state transition at a time. This is the single
public Recurspec skill; load its phase references only when the current state requires
them.

## Route by current state

Inspect the request and repository, then take the first matching route:

| State | Route |
|---|---|
| Raw goal or missing contract tree | Read and follow `references/design.md` |
| Leaf lacks a verified technology resolution | Read and follow `references/resolve.md` |
| BUY or ADOPT leaf | Verify its seam; stop at the procurement boundary |
| DEFER leaf | Publish a Research Frontier with `recurspec frontier publish`; stop until it resolves |
| Ready BUILD or WRAP leaf | Run the candidate cycle below |
| Prior REVERT | Repair from the latest Negative Patterns |
| Implemented or merged change | Read and follow `references/reconcile.md` |

After each route, classify the new state again. Continue while the next transition is
safe and in scope. Stop at `PASS`, `DEFER`, `ESCALATE`, or a decision that genuinely
requires the user. Keep process debt in one `ROADMAP.md`.

## Authority seam

- The **Architect** owns contracts, bounded handoffs, verification, keep/revert/escalate,
  reconciliation, and the final report.
- The **Implementor** owns source and tests on an isolated candidate branch. It cannot
  change the target contract or authorize its own merge.
- Maker and checker must differ. If an independent checker is unavailable, report that
  limitation and require human review.

## Candidate cycle

1. Create `.recurspec/handoffs/strategy-<ticket-id>.md` with the target contract, goal,
   non-goals, EARS invariants, checks, baseline, and gates.
2. Create an isolated `candidate/<ticket-id>` worktree and give the Implementor only the
   strategy handoff. Implement test-first.
3. On repair, read branch-scoped Negative Patterns and localize the failure through the
   code graph or stack trace. Do not retry an invalidated approach.
4. Have an independent checker run:

   ```text
   recurspec evaluate <module> candidate/<ticket-id> \
     --worker-state .recurspec/worker-authorizations.json \
     --authorization-id <completed-node-id>
   ```

5. Apply the result:
   - `KEEP` (`0`): merge, reconcile, then explicitly promote the baseline by rerunning
     with `--record-baseline` after the merge.
   - `REVERT` (`1`): revert the candidate and create a correction handoff quoting the
     latest Negative Pattern.
   - evaluation error (`2`): repair the instrument; this is not product evidence.
   - `ESCALATE` (`3`): block the ticket and stop automatic repair.

The defaults escalate after five consecutive reverts or eight total reverts on one
candidate branch.

## Evaluation contract

`modules/<name>/measure.sh` may emit one metric or a `"metrics"` list. Untagged metrics
default to `hard_gate`.

| Tier | Keep rule |
|---|---|
| `hard_gate` | Unknown or regression blocks |
| `target` / `optimization` | Regression beyond tolerance blocks; neutral keeps |
| `observation` | Record only; never blocks |

KEEP authorization and baseline promotion are separate acts.

## CLI surface

These commands exist on the installed `recurspec` package. Use them; do not invent
parallel scripts.

| Command | When |
|---|---|
| `recurspec contract check PATH` | Validate one node or a Contract Tree |
| `recurspec structure check REPO` | Detect uncontracted symbols and §6 drift |
| `recurspec stack check REPO` | Audit §8 fields and pins |
| `recurspec reconcile plan REPO` | Draft-only Structural Feedback actions |
| `recurspec evaluate MODULE BRANCH ...` | Isolated Candidate keep/revert/escalate |
| `recurspec modules check REPO --changed-file PATH` | Run `checks.sh`/`measure.sh` for touched modules |
| `recurspec frontier publish TREE` | Write Research Frontier tickets (optional `--remote github`) |
| `recurspec frontier check REPO` | Verify every ticket still points at a Contract Node |
| `recurspec corpus export --output FILE --i-opt-in` | Redacted decision corpus; refuses without `--i-opt-in` |
| `recurspec skills install --target grok` | Install this skill to `$GROK_HOME/skills` |

Optional extra `recurspec[runtime]` pins the packet-only Messages adapter. The Worker
Pool still requires an injected `RuntimeCall`; do not give a worker a filesystem path.

## Close-out

After KEEP, follow `references/reconcile.md` and emit:

```text
TICKET:        <id>
CONTRACT:      <path>
BASELINE:      <metric vector before>
FINAL:         <metric vector after>
ITERATIONS:    <revert count before KEEP>
VERIFICATION:  checks.sh <result> · measure.sh <result> · telemetry <result>
UNVERIFIED:    <human judgment or path no gate exercised; never empty by default>
RESULT:        READY FOR HUMAN REVIEW
```

Tests and measurements are `Sampled` or `Measured`, never `Proved`.
