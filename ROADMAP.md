# Recurspec roadmap

This is the sole incomplete-work registry. Completed work belongs in
[CHANGELOG.md](./CHANGELOG.md) and git history.

Statuses: `ready`, `blocked`, `research`, `deferred`.

## Outcome validation

These studies are required before claiming that Recurspec improves engineering outcomes.
The cited foundations motivate individual mechanisms; they do not validate Recurspec as a
whole.

| ID | Study | Status | Acceptance criterion |
|---|---|---|---|
| R-400 | Two real-project case studies | research | Reproducible before/after repositories and decision logs; no outcome data yet |
| R-401 | Procurement-seam effectiveness | research | Measure avoided custom code and later replacement cost; no outcome data yet |
| R-402 | Negative Pattern effectiveness | research | Compare repeated-failure rate with and without repair memory; no outcome data yet |
| R-403 | Contract drift effectiveness | research | Compare detected and escaped code/contract mismatches; no outcome data yet |

## Long horizon

| ID | Outcome | Status | Blocked by |
|---|---|---|---|
| R-501 | Learn reusable failure predictors from Negative Patterns | blocked | R-400, R-402, R-500 |
| R-502 | Recommend Decision Classes from comparable outcomes | blocked | R-401, R-500 |

## Intentionally out of scope

- A web interface before the CLI and contract schema stabilize.
- Model-judge scores as autonomous merge authority.
- Claims of formal proof from tests, measurements, or model consensus.
- Centralized telemetry without explicit project-level opt-in.
