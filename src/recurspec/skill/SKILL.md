---
name: recurspec
description: Design and improve software through recursive contracts, technology resolution, isolated implementation, evidence evaluation, and reconciliation. Use with a raw goal, contract node, implementation ticket, failed candidate, or completed change.
---

# Recurspec

Advance a system by one evidence-backed state transition at a time. This is the single
public Recurspec skill; load its phase references only when the current state requires
them.

## First action

Before reading a phase reference or editing contracts, run:

```text
recurspec status .
```

Use the printed `tree` and `route`. Do not infer Recurspec readiness from a `SYSTEM.md`
file, a crate map, or a rival registry such as `FEATURE_GAPS.md`.

| `tree` | `route` | What to do |
|---|---|---|
| `missing` | `design` | Follow `references/design.md`. Create the Contract Tree and `ROADMAP.md`. |
| `not_recurspec` | `design` | Follow `references/design.md`. Existing `SYSTEM.md` is source material, not a Contract Node. Do not stamp the version marker onto an incomplete file. Create `ROADMAP.md` even if another incomplete-work file exists. |
| `invalid` | `repair` | Run `recurspec contract check` and fix diagnostics. Do not implement product code first. |
| `valid` | `ready` | Then take the first matching request route below. |

If `missing_probes` is non-empty, `route` is `repair` even when `tree` is `valid`: write
those scripts or remove the §7 claim. If `extra_trees` lists `.recurspec/contracts`,
classify that tree too; do not ignore a second Contract Tree.

This first action still runs when the user asked for a paper, skill install, or
research. Status the *subject* repository (the software being written about), not only a
new folder you created. A `missing` tree on a prose-only preprint directory is expected;
do not invent a Contract Tree for a paper.

Keep process debt in one `ROADMAP.md`. A rival file may be cited from `ROADMAP.md`; it
does not replace it.

## Work lists fan out

A numbered or bulleted list is not one Contract Node and not one candidate. After
`recurspec status`, split the list so each item can fail independently and receive its
own FRAME → RESEARCH → RESOLVE pass.

```text
recurspec fanout --item "..." --item "..."
recurspec fanout --list-file work.md --write
```

For each item:

1. Give it a ROADMAP id and a `strategy-<id>.md` handoff.
2. Load only that handoff plus the target contract into the implementor.
3. Do not keep sibling items in the same packet.
4. If parallel workers exist, dispatch one worker per item after the split.

Do not implement 1–N in a single pass because they arrived in one message.

## Route by current state

After `recurspec status` reports `ready`, take the first matching route:

| State | Route |
|---|---|
| Raw goal or missing contract tree | Read and follow `references/design.md` |
| Leaf lacks a verified technology resolution | Read and follow `references/resolve.md` |
| BUY or ADOPT leaf | Verify its seam; stop at the procurement boundary |
| DEFER leaf | Publish a Research Frontier with `recurspec frontier publish`; stop until it resolves |
| Ready BUILD or WRAP leaf | Run the candidate cycle below |
| Prior REVERT | Repair from the latest Negative Patterns |
| Implemented or merged change | Read and follow `references/reconcile.md` |

After each route, classify the new state again with `recurspec status` when the tree
changed. Continue while the next transition is safe and in scope. Stop at `PASS`,
`DEFER`, `ESCALATE`, or a decision that genuinely requires the user. Keep process debt
in one `ROADMAP.md`.

## Authority seam

- The **Architect** owns contracts, bounded handoffs, verification, keep/revert/escalate,
  reconciliation, and the final report.
- The **Implementor** owns source and tests on an isolated candidate branch. It cannot
  change the target contract or authorize its own merge.
- Maker and checker must differ. If you produced the candidate in this session, you
  cannot KEEP it. If an independent checker is unavailable, report `NEED_CHECKER` and
  require human review.

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
| `recurspec status REPO` | First action: classify `missing` / `not_recurspec` / `invalid` / `valid` |
| `recurspec fanout --item ...` | Split a work list into one strategy handoff per item |
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

Evidence Stage is maturity. Evidence *class* is what a signal may license. Do not let
one class stand in for another.

| Class | Licenses | Does not license |
|---|---|---|
| Executed behavior (tests) | Exercised cases satisfied their oracles | General correctness or product outcome |
| Static structure | Inspected artifact satisfied those rules | Runtime behavior |
| Empirical measurement | This workload in this environment | A different workload or scale |
| Model judgment | Named model and rubric produced this assessment | Ground truth or merge authority |
| Human decision | An accountable person accepted residual risk | That the decision was correct |

End any effectiveness claim with an explicit boundary. "No data yet" is a complete
finding. Never invent a metric. If the user asks whether the system "works" or is
"better" and no outcome study exists, say it is research-informed, not
research-validated.
