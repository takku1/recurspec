# R-400 case record — graphgraph / DX-WDAC-01

**Status: observational case record. This is not R-400 outcome data and must not be
counted toward the six-pair stopping rule in
[evaluation-protocol.md](./evaluation-protocol.md) §7.**

R-400 asks for *matched pairs*, assigned before either arm starts, with an independent
checker. This ticket was worked without a matched baseline task, without a pre-declared
time estimate, and — in its final pass — without maker/checker separation. It is written
up because the ticket produced one clean instance of R-400's *primary* measure (a
contract/code mismatch caught before merge by the Structure Gate) and one instance of the
failure mode `graphgraph-01` already flagged post-hoc (an accept whose verification scope
was narrower than the change). Recording those as a case record is honest; folding them
into R-400's result would not be.

- Protocol version: 2026-08-14
- Subject project: `C:/Users/dcarn/aiprojects/graphgraph` (eligible under §2 — not
  Recurspec itself)
- Ticket: `DX-WDAC-01`
- Contract:
  `docs/architecture/agent-interfaces/cli-transport/environment-commands/SYSTEM.md`
- Baseline commit: `6f6b013` (2026-08-20 12:08:06 -0400)
- Candidate commit: `11c7e25` (2026-08-20 19:39:26 -0400), branch
  `candidate/dx-wdac-01`, unmerged

## 1. Admissibility against the pre-registration

| Protocol condition | Met? | Why |
|---|---|---|
| §2 Subject project is not Recurspec | yes | graphgraph is an independent repository |
| §2 Task is real and independently prioritized | yes | reproduced on the maintainer's own machine: Windows Application Control blocks the generated `graphgraph.exe` launcher, breaking setup |
| §2 Decomposes into ≥3 Contract Nodes | **no** | the whole ticket lives in one existing leaf contract |
| §3 Matched task of similar a-priori scope | **no** | no second task was selected |
| §3 Condition assigned before either arm starts | **no** | no coin flip; there was no baseline arm to assign |
| §3 A-priori time estimate recorded before start | **no** | never recorded |
| §5 Structure Gate ran on the Recurspec arm | yes | `recurspec structure check . --source-root src/graphgraph` |
| §10 Maker ≠ checker | **partial** | the first checker pass was independent; the final pass was not (see §5) |

Three of the four design conditions fail. The correct classification is a **within-project
case record**, not a matched pair.

## 2. The ticket

`graphgraph --version` resolves to a generated console-script launcher that Windows
Application Control refuses, while `python -m graphgraph --version` succeeds in the same
process environment. Setup executed that launcher for MCP registration and for its final
verification step, so a healthy install failed at the last step with a policy error and no
stated next step.

The fix routes setup through the created environment's interpreter with `-m graphgraph`,
and adds a `[CLI Launcher]` section to `graphgraph doctor` that probes only the exact
`shutil.which("graphgraph")` path — no shell, bounded timeout — and prints the
`python -m graphgraph` fallback when that launcher is unusable.

## 3. Timeline (file mtimes and commit timestamps, all 2026-08-20 -0400)

| Time | Event |
|---|---|
| 12:08:06 | baseline `6f6b013` on `main` |
| 12:36:55 | strategy handoff `strategy-DX-WDAC-01.md` written (contract, invariants, gates) |
| — | implementor work, uncommitted in `.scratch/worktrees/candidate-dx-wdac-01` |
| 14:09:09 | correction handoff `correction-DX-WDAC-01.md` — **Structure Gate rejection** |
| 14:09–19:39 | idle; the worktree sat uncommitted between sessions |
| 19:39:26 | candidate `11c7e25` committed after the second correction |

**Wall-clock is not reportable as a work-time measure here.** The 7h31m span contains a
multi-hour idle gap between two sessions, and Recurspec's Job Store — the §5 data source
for elapsed time — was not driving this ticket. Reporting the span as a duration would be
a number with no referent.

## 4. Outcome measures (protocol §5)

| Measure | Value | Source |
|---|---|---|
| **Primary:** contract/code mismatches caught before merge | **1** | see §5.1 |
| **Primary:** mismatches that escaped | unknown | 30-day window has not elapsed; candidate is unmerged |
| Wall-clock to first accepted implementation | not reportable | §3 |
| Review round-trips | **2** | one independent (§5.1), one not (§5.2) |
| Reverted or redone work | **0** | no revert; both round-trips were corrections applied on top |
| Decision Class later reversed | n/a | no procurement decision (R-401) |
| Repeated a previously-failed approach | n/a | no failed Candidate attempt (R-402) |
| Failed-to-help (§6) | no | reached a verified candidate; tree never abandoned |
| Manual Evaluation Gate override | none | the formal gate was never reached — see §6 |

### 4.1 Baseline-arm cells

Every baseline column is **absent, not unknown**. There is no baseline arm. The
`graphgraph-01` log's convention of writing `unknown` in baseline cells is not used here,
because `unknown` implies a measurement that could still be taken.

## 5. The two round-trips

### 5.1 Structure Gate catch — the primary measure, independently checked

The implementor added a new regression file, `tests/test_setup_bootstrap.py`, that no
Contract Node declared. `recurspec structure check . --source-root src/graphgraph`
rejected the candidate, and `recurspec reconcile plan` emitted one `test_seam_review`
action naming that file.

This is precisely R-400's primary measure: a contract/code mismatch caught **before**
merge by the Structure Gate, on a change whose test suite was otherwise green. The
correction updated the leaf contract to declare the new setup invariant, add
`setup_graphgraph.py` to its implementation files, and add the new test to its seam. After
it, `structure check` returned `PASS` and `reconcile plan` returned `{"actions": []}`.

Worth stating plainly: the mismatch was *bookkeeping*, not a behavioral defect. The gate
caught an undeclared test seam, not a bug. R-400's primary measure counts it, and that is
what the measure is defined to count — but a case record that let this read as "the gate
caught a bug" would be overstating it.

### 5.2 Behavioral defect found on review — **not independently checked**

The second pass found a real behavioral gap the first pass did not. The launcher probe
reported only the `OSError` form of a blocked launcher. Two other outcomes — a launcher
that starts and exits non-zero, and a launcher absent from `PATH` — fell through every
branch and printed an **empty `[CLI Launcher]` section**: no diagnosis, no fallback. That
is the one outcome that strands a user, and it is the exact condition the contract's
invariant names (*"IF the PATH-selected launcher cannot be executed THEN doctor SHALL …
identify the launcher as unusable, and print an exact `python -m graphgraph` fallback"*).

Confirmed by direct probe before the fix: with `subprocess.run` returning
`CompletedProcess(returncode=1, stderr="Application Control policy has blocked this
file")`, the rendered `[CLI Launcher]` section was empty and contained no fallback.

Both outcomes now report as unusable, pinned by two red controls. Red-capability was
proven by mutation: with the two new branches removed, exactly the two new tests fail and
the three pre-existing launcher tests still pass.

**This round-trip violates §10's maker/checker separation.** The same agent wrote the fix,
wrote its tests, and judged the result. Its findings are recorded as observations, not as
a gate verdict.

## 6. Verification actually run on the candidate

| Check | Result |
|---|---|
| `pytest tests/test_cli_mcp.py tests/test_setup_bootstrap.py tests/test_distribution_artifacts.py` | 109 passed, 4 subtests passed |
| `pytest tests/` (full suite) | **1291 passed, 5 skipped, 1 xfailed** |
| `ruff check` on all five changed Python files | all checks passed |
| `recurspec structure check . --source-root src/graphgraph` | PASS |
| `recurspec reconcile plan --format json` | `{"actions": [], "deferred_empirical_events": 0}` |
| `git diff --check` | clean |
| Mutation check on the two new red controls | both fail without the fix |

All test runs used `PYTHONPATH=<worktree>/src`. Without it the worktree's bare `pytest`
resolves `graphgraph` to the **main** checkout's editable install and silently exercises
the wrong code — verified in this session
(`graphgraph.__file__` pointed at `C:/Users/dcarn/aiprojects/graphgraph/src/...` from
inside the candidate worktree). Any future arm run out of a `.scratch/worktrees/*`
directory must set it or its verification evidence is void.

**The formal Evaluation Gate did not run.** `recurspec evaluate` requires a worker
authorization that this project does not have, so the maximum verdict available locally is
`READY FOR HUMAN REVIEW`. Every §5 number above comes from the checks in this table, not
from a gate decision.

## 7. What this record licenses

- One dated instance of the Structure Gate catching a contract/code mismatch before merge,
  on a real ticket, with the rejecting command and the clearing command both recorded.
- One replication of `graphgraph-01`'s post-hoc finding that **an accept is only as good as
  its verification scope**: the first pass ran a green focused suite and a green structure
  check, and still left a contract invariant unsatisfied on two of four branches. Two
  independent case records now point at the same gap.
- A reproducible before/after: `6f6b013` → `11c7e25`, with the failing probe in §5.2
  runnable against the baseline.

## 8. What this record does not license

- Any comparative claim. There is no baseline arm, so nothing here compares Recurspec's
  workflow to graphgraph's existing one.
- Any contribution to R-400's stopping rule, sample, or eventual result.
- Any claim that the Structure Gate catches *behavioral* defects — the catch in §5.1 was an
  undeclared test seam, and the behavioral defect in §5.2 was found by reading the diff
  against the contract, not by any gate.
- Any effectiveness claim at all. Recurspec remains research-informed, not
  research-validated ([evidence-cycle.md](../process/evidence-cycle.md)).

## 9. Converting this into an admissible R-400 pair

DX-WDAC-01 cannot be retrofitted — §3 forbids choosing the comparison after seeing how a
task went. A future pair on this project would need, before either task starts:
`recurspec study init` with two tasks of matched a-priori scope, `recurspec study assign`
to coin-flip the condition, an a-priori time estimate written down, and a checker who is
not the implementor for `recurspec study accept`. graphgraph's ROADMAP currently carries
several `ready` rows of comparable scope (for example `OW-SH-01` and `OW-D-04`) that would
serve.
