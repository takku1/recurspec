---
name: recurspec
description: Design and improve software through recursive contracts, technology resolution, isolated implementation, evidence evaluation, and reconciliation.
---

# Recurspec

Advance one evidence-backed transition at a time:

`DISCOVER -> RESOLVE -> EXECUTE -> CHECK -> RECONCILE`

## Controller

1. Run `recurspec status .` on the *subject* repository before design, research, a
   paper, or a skill install. Treat `missing` and `not_recurspec` as design routes;
   existing prose is source material, not a finished Contract Tree. A prose-only preprint
   needs no invented tree.
2. Repair `invalid`, `missing_probes`, and every separately reported tree such as
   `.recurspec/contracts` before product code. Then take the first applicable route:
   - raw goal or missing tree -> [design](references/design.md)
   - unresolved technology -> [resolve](references/resolve.md)
   - `BUY` or `ADOPT` -> verify the Procurement Seam and stop
   - `DEFER` -> record/publish its Research Frontier and stop
   - ready `BUILD` or `WRAP` -> Candidate cycle below
   - implemented or merged change -> [reconcile](references/reconcile.md)
3. Split every multi-item request with `recurspec fanout`; each independently failing
   item gets one Contract Node, handoff, and one Candidate. Do not give sibling items to
   the same implementor packet.
4. Repeat status after each safe transition. Stop at `PASS`, `DEFER`, `ESCALATE`,
   `NEED_CHECKER`, or a decision that genuinely requires the user.

## Candidate cycle

The Architect owns the Contract Tree, `ROADMAP.md`, handoff, final decision,
reconciliation, and report. An Implementor works test-first on an isolated
`candidate/<ticket>` branch and cannot change the target contract. A different checker
must approve the exact Candidate commit before:

```text
recurspec evaluate <module> candidate/<ticket> \
  --worker-state .recurspec/worker-authorizations.json \
  --authorization-id <completed-node-id>
```

The Evaluation Gate returns only `KEEP`, `REVERT`, or `ESCALATE`. Instrument failure is
an error, not a fourth outcome. `ESCALATE` means the Contract Node or search space may be
wrong. `KEEP` may merge, but Best Known State promotion remains a separate explicit
post-merge evaluation. On `REVERT`, repair from the latest Negative Pattern; do not retry
an invalidated approach.

## Non-negotiable boundaries

- `ROADMAP.md` is the sole incomplete-work registry; caches, handoffs, tickets, and
  relationship indexes are derived.
- Resolve `BUY | ADOPT | WRAP | BUILD | DEFER` before decomposition. Never decompose a
  vendor's internals.
- Missing, ambiguous, contradictory, malformed, or non-finite evidence fails closed.
  Never invent a vendor, version, price, feature, metric, or numeric default.
- Tests license only the exercised cases satisfying their oracles. Runtime measurements license
  only that workload and environment. Neither licenses general correctness or
  product outcomes; only formal proof is `Proved`.
- Model judgment may propose `Unknown` or `Inferred` Coverage Review findings; it cannot
  mutate the Contract Tree or authorize merge.
- If no outcome study exists, call Recurspec research-informed, not
  research-validated. Every effectiveness claim names its evidence boundary.

## Close-out

Report ticket, contract, baseline, final metric vector, iterations, executed checks,
unverified judgments, and `RESULT: READY FOR HUMAN REVIEW`. Never label tests or
measurements `Proved`.
