# Case-study decision log (R-400–R-403)

Use one copy of this file per matched task pair. Fill it **before** either task
starts, except the outcome rows. Do not invent numbers. If a field is unknown,
write `unknown` — never a default metric.

This is apparatus, not results. Recurspec's own repository is excluded from the
task population ([evaluation-protocol.md](./evaluation-protocol.md) §2).

## Pre-registration binding

- Protocol version / date:
- Pair id:
- Project (not recurspec itself):
- Assignment method (coin flip / first-picked) and result:
- A-priori time estimate for each task (set before either starts):

## Tasks

| Arm | Task name | Scope estimate | Condition |
|---|---|---|---|
| Recurspec | | | Contract Tree + Decision Class + Evaluation Gate |
| Baseline | | | Project's existing workflow, described as it is |

## Baseline workflow (as it really is)

- Artifacts that precede implementation:
- Review that happens:
- How rework is handled:

## Outcomes (fill only as observed)

| Measure | Recurspec arm | Baseline arm | Source |
|---|---|---|---|
| Wall-clock to first accepted implementation | | | Recurspec: Job Store `claims.claimed_at` vs accept commit. Baseline: hand-timed. |
| Review round-trips | | | decision log |
| Reverted or redone work | | | Recurspec: evidence log. Baseline: hand-logged. |
| Structure-Gate diagnostics caught before merge | | n/a (gate does not run) | `check_structure` list |
| Escaped mismatches within 30 days | | | hand-logged; no automated source |
| Decision Class later reversed? cost? | | | hand-logged (R-401) |
| Repeated a previously-failed approach? | | n/a | Negative Pattern ablation (R-402); Recurspec arm only |
| Failed-to-help? (2× time or tree abandoned) | | | protocol §6 |

## Manual Evaluation Gate overrides

| When | Gate would have | Human did | Reason |
|---|---|---|---|

## Arm start (observed, not a-priori)

- Recurspec arm started: not started
- Baseline arm started: not started
- Accepted implementation: no. Do not fill wall-clock until an independent accept.

## Post-hoc metrics

List any number reported that is not in the protocol §5 table. Label each `post-hoc`.
