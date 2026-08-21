# Case-study decision log (R-400–R-403)

Use one copy of this file per matched task pair. Fill it **before** either task starts, except the outcome rows. Do not invent numbers. If a field is unknown, write `unknown` — never a default metric.

This is apparatus, not results. Recurspec's own repository is excluded from the task population ([evaluation-protocol.md](../evaluation-protocol.md) §2).

## Pre-registration binding

- Protocol version / date: 2026-08-14
- Pair id: `graphgraph-02`
- Project (not recurspec itself): `C:/Users/dcarn/aiprojects/graphgraph`
- Assignment method (coin flip / first-picked) and result: coin flip via secrets.randbelow(2); Recurspec arm = R-003 Abstention cannot prove absence for a query built only of short or definition-shaped words; Baseline arm = R-004 Facet reservations are seated in arrival order, so a recovered answer can land at the bottom of the packet
- A-priori time estimate for each task (set before either starts): 4h each (one session)

## Tasks

| Arm | Task name | Scope estimate | Condition |
|---|---|---|---|
| Recurspec | R-003 Abstention cannot prove absence for a query built only of short or definition-shaped words | 4h each (one session) | Contract Tree + Decision Class + Evaluation Gate |
| Baseline | R-004 Facet reservations are seated in arrival order, so a recovered answer can land at the bottom of the packet | 4h each (one session) | Project's existing workflow, described as it is |

## Baseline workflow (as it really is)

ROADMAP.md is the sole incomplete-work registry, with docs/open-work.md and .scratch/wayfinder-map/MAP.md alongside it; implement directly on main; pytest tests/ plus gray-box measurement cycles serve as review; rework is additional commits on main; independent checker passes happen ad hoc and items sit marked NEED_CHECKER until one runs. No Recurspec Contract Tree, Decision Class, Structure Gate, or isolated candidate branch.

## Outcomes (fill only as observed)

| Measure | Recurspec arm | Baseline arm | Source |
|---|---|---|---|
| Wall-clock to first accepted implementation | unknown | unknown | |
| Review round-trips | unknown | unknown | |
| Reverted or redone work | unknown | unknown | |
| Structure-Gate diagnostics caught before merge | unknown | n/a | |
| Escaped mismatches within 30 days | unknown | unknown | |
| Decision Class later reversed? cost? | unknown | unknown | |
| Repeated a previously-failed approach? | unknown | n/a | |
| Failed-to-help? (2× time or tree abandoned) | unknown | unknown | |

## Manual Evaluation Gate overrides

| When | Gate would have | Human did | Reason |
|---|---|---|---|

## Arm start (observed, not a-priori)

- Recurspec arm started: not started
- Baseline arm started: not started
- Accepted implementation: no. Do not fill wall-clock until an independent accept.

## Post-hoc metrics

List any number reported that is not in the protocol §5 table. Label each `post-hoc`.
