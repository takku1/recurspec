# Case-study decision log (R-400–R-403)

Use one copy of this file per matched task pair. Fill it **before** either task starts, except the outcome rows. Do not invent numbers. If a field is unknown, write `unknown` — never a default metric.

This is apparatus, not results. Recurspec's own repository is excluded from the task population ([evaluation-protocol.md](../evaluation-protocol.md) §2).

## Pre-registration binding

- Protocol version / date: 2026-08-14
- Pair id: `graphgraph-01`
- Project (not recurspec itself): `C:/Users/dcarn/aiprojects/graphgraph`
- Assignment method (coin flip / first-picked) and result: coin flip via secrets.randbelow(2); Recurspec arm = OW-AC-06 Machine-response token surface (response <= 1.15x evidence-packet tokens); Baseline arm = OW-AC-09 Contract and telemetry consistency (machine-readable capability identity)
- A-priori time estimate for each task (set before either starts): 4h each (one session)

## Tasks

| Arm | Task name | Scope estimate | Condition |
|---|---|---|---|
| Recurspec | OW-AC-06 Machine-response token surface (response <= 1.15x evidence-packet tokens) | 4h each (one session) | Contract Tree + Decision Class + Evaluation Gate |
| Baseline | OW-AC-09 Contract and telemetry consistency (machine-readable capability identity) | 4h each (one session) | Project's existing workflow, described as it is |

## Baseline workflow (as it really is)

docs/open-work.md + .scratch/wayfinder-map/MAP.md; implement on current branch; pytest and gray-box cycles as review; rework is more commits. No Recurspec evaluate.

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

## Post-hoc metrics

List any number reported that is not in the protocol §5 table. Label each `post-hoc`.
