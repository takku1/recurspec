# Contract reconciliation

Reconciliation compares the accepted Contract Tree with implementation and evidence, then
proposes which representation should change. It is draft-only: the Architect reviews all
contract mutations.

Module contract:
[Contract Reconciler](../architecture/contract-reconciler/SYSTEM.md).

## Finding to action

| Finding | Typical trigger | Reviewable action |
|---|---|---|
| Code drift | Public source has no owning Contract Node | Draft an `Unknown` leaf |
| Structural bloat | One contract owns separable interfaces | Propose an interface-driven split |
| Test-seam drift | A new mock or adapter is undeclared | Review the parent Interface Contract |
| Metric drift | Behavior contradicts a target or assumption | Review code, contract, instrument, or Research Frontier |
| Coverage gap | Bounded Coverage Review finds a missing seam | Propose an `Unknown` or `Inferred` node/interface |

All checkers may report through a common Finding envelope, but their evidence policies
remain typed. Static structure cannot establish runtime behavior. A metric cannot rewrite
its own target to turn failure into success. Contradictory evidence refuses a plan.

## Rules

1. Prefer interface-driven splits over arbitrary line cuts.
2. Never invent requirements during drafting; state the Evidence Stage and the evidence
   needed to advance it.
3. Keep one-parent ownership in the Contract Tree. Cross-node dependencies belong in a
   regenerable Relationship Index.
4. Keep incomplete intent in `ROADMAP.md`; generated drafts and Research Frontier tickets
   reference it rather than becoming a competing backlog.
5. Reconciliation may remove, merge, or reprioritize future work when evidence makes it
   unnecessary.
6. The Evaluation Gate remains the only authority for Candidate `KEEP`, `REVERT`, or
   `ESCALATE` decisions.

Run the current draft-only interface with:

```bash
recurspec reconcile plan . --changed-file src/example.py
```

Exit `0` means no action, `1` means reviewable actions exist, and `2` means the
instrument could not produce trustworthy findings.
