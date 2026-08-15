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
| Wall-clock to first accepted implementation | ~22 min (2026-08-15 01:11 first edit -> 01:33 accept) | unknown | mtime of `response_surface.py` -> checker accept, this session |
| Review round-trips | 1 (checker found & fixed a JSON-corruption regression after accept, before considering `--record-baseline`) | unknown | commits `64a0600` -> `799dd1c` |
| Reverted or redone work | 0 reverted; 1 corrective commit on top of the accepted candidate (not a revert) | unknown | |
| Structure-Gate diagnostics caught before merge | unknown | n/a | |
| Escaped mismatches within 30 days | unknown | unknown | |
| Decision Class later reversed? cost? | unknown | unknown | |
| Repeated a previously-failed approach? | unknown | n/a | |
| Failed-to-help? (2× time or tree abandoned) | unknown | unknown | |

## Manual Evaluation Gate overrides

| When | Gate would have | Human did | Reason |
|---|---|---|---|

## Arm start (observed, not a-priori)

- Recurspec arm started: 2026-08-15 after assignment (not accepted; NEED_CHECKER)
- Recurspec arm work this session: `response_surface.clamp_response_to_packet_surface` drops ROUTE/ANCHORS/JSON wrappers when `estimate_tokens(response) > 1.15 * estimate_tokens(packet)`. Wired at the end of `_compile_response`. Tests in `tests/test_response_surface.py`.
- Baseline arm started: 2026-08-15. OW-AC-09: `capability_identity()` + `project_status.capability.contract_id` on the MCP transport, tested (`tests/test_mcp_machine_contract.py`, 6/6 pass). CLI parity (ADR-AI-002) intentionally left open. Committed `55c4f53`, doc status `70309e5`. Plain workflow -- no Recurspec contract/gate touched.
- Accepted implementation: yes, with a correction. Recurspec arm accepted 2026-08-15 ~01:33 by checker dillon.c.carney@gmail.com (independent of implementor session), committed `64a0600`. Checker ran only `pytest tests/test_response_surface.py` (2 passed) before accepting -- the implementor's own log had run the same narrow scope. Running the full suite afterward (`pytest tests/`) found 31 failures caused by the accepted change; one class (JSONDecodeError / KeyError on `--json` calls, 5 tests) was a clear bug and is fixed in `799dd1c`. The remaining ~26 failures are a genuine spec conflict, not a bug: for small graphs the fixed envelope overhead (control/actionable/routing/metrics) exceeds 1.15x the packet, so OW-AC-06's clamp correctly drops to a reduced payload -- but several other tests assert the full envelope is always present. Unresolved; needs a scoping decision (exempt `json_output` callers from the ratio? floor the ratio below some minimum packet size? update the envelope-completeness tests?) before `--record-baseline` should be run.

## Post-hoc metrics

List any number reported that is not in the protocol §5 table. Label each `post-hoc`.

- post-hoc: **Accept-time verification gap.** The checker accepted `64a0600` after running only `tests/test_response_surface.py` (the new file's own tests), matching the implementor's own verification scope. Running the full suite (`pytest tests/`, 2026-08-15) surfaced 31 unrelated-looking failures the narrow run could not have caught. Protocol lesson: an "accept" should require at least one full-suite run, not just the candidate's own new tests, or wall-clock/round-trip counts understate the true review cost.
