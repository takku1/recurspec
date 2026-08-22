# Project fit and progressive adoption

Recurspec is useful when the cost of architectural drift, repeated failed approaches, or
unsafe self-evaluation exceeds the cost of maintaining explicit contracts. It is not a
default requirement for every repository.

## Quick fit check

Add one point for each true statement:

- The system has at least three independently failing modules or external dependencies.
- Multiple people or agent sessions change it over time.
- Incorrect changes can cause security, financial, data-loss, or operational harm.
- Performance or resource use is a product constraint rather than a preference.
- Build-versus-buy decisions materially affect liability, cost, or replacement effort.
- Requirements and implementation have already drifted or been repeatedly rediscovered.

| Score | Recommendation |
|---:|---|
| 0–1 | Skip Recurspec; tests and a short README are probably enough. |
| 2–3 | Use `contract check` only at important boundaries. |
| 4–5 | Add `evaluate` for risky or measurable modules. |
| 6 | Consider the full isolated maker/checker and reconciliation loop. |

This rubric is onboarding guidance, not an empirically validated predictor. Record cases
where its recommendation is wrong so it can later be calibrated.

## Three adoption depths

### 1. Check only

Start with orientation, then write one versioned Contract Node for the highest-risk
boundary:

```bash
recurspec status .
recurspec contract check path/to/SYSTEM.md
```

If `status` reports `not_recurspec`, existing `SYSTEM.md` files are source material, not
Recurspec contracts. Do not stamp the version marker onto an incomplete file.

Expand into a Contract Tree only when responsibilities can fail independently. You do
not need Candidates, metrics, or the full vocabulary to gain structural validation.

### 2. Check and evaluate

Add `checks.sh` and `measure.sh` only to modules whose non-functional behavior matters.
Use `recurspec evaluate` to prevent correctness or metric regressions. Keep baseline
promotion explicit.

### 3. Full loop

Use isolated Candidates, distinct maker/checker identities, Negative Pattern repair
memory, and contract reconciliation when changes are long-lived, parallel, or expensive
to get wrong. That loop is implemented. Whether it improves outcomes is unfinished work
in [ROADMAP.md](../ROADMAP.md), not a missing orchestrator.

## Stop rule

If maintaining a Contract Node costs more than the decisions, drift, or failed work it
prevents across two meaningful changes, simplify it or remove it. Ceremony is not itself
evidence of quality.
