# Evaluation protocol (pre-registration)

**Status:** Pre-registered 2026-08-14. No outcome data has been collected under this
protocol as of this version. Any revision made after data collection begins must be
recorded below as a dated, reasoned amendment, not a silent edit — this is the same rule
Registered Reports enforce and that [foundations.md §9](./foundations.md#9-pre-registration-precedent-for-effectiveness-claims)
cites as precedent.

This protocol does not itself establish that Recurspec improves anything. It exists so
that [ROADMAP.md](../../ROADMAP.md) items R-400 through R-403 can be run against a
public, dated commitment instead of a plan written after seeing the results.

## 1. Scope

Covers R-400 (real-project case studies), R-401 (procurement-seam effectiveness), R-402
(Negative Pattern effectiveness), and R-403 (contract-drift effectiveness). Does not
cover R-404 (a domain-general example is a deliverable, not a comparative claim) or R-204
(an engineering task, not an effectiveness study).

## 2. Task population

An eligible task is a real, unresolved software goal that (a) has enough scope to
decompose into at least three Contract Nodes under Recurspec, and (b) has a deadline or
priority that exists independent of this research — never a task manufactured for the
study. Eligible projects are a convenience sample: repositories the maintainer directly
works on or is explicitly granted access to for this purpose. Recurspec's own repository
is excluded from the population, since it is the tool's own construction and dogfooding
it is not an independent case. This is not a random sample of software projects, and any
report must state that limitation rather than omit it.

## 3. Design: matched-pair, not a randomized controlled trial

Recurspec does not have access to a developer pool comparable to a resourced RCT (contrast
[foundations.md §10](./foundations.md#10-a-disclosed-methodology-human-baseline-precedent),
which describes METR's 16-developer trial as a precedent this project cannot reproduce at
its current scale). The design here is matched-pair and within-project: for each
participating project, select two tasks of similar estimated scope, matched by an
a-priori time estimate made before either task starts. One task is implemented through
the full Recurspec workflow (Contract Tree, Decision Class, Evaluation Gate); the other
through the project's existing workflow, unchanged. Which task gets which condition is
decided before either task starts (for example by a coin flip, or by whichever task is
picked up first) and recorded either way, to prevent choosing the comparison after seeing
how a task went. This is a quasi-experimental design and must be reported as such, not
inflated to "controlled trial."

## 4. Comparator workflow

The baseline is each project's actual pre-existing workflow, described in the case-study
writeup as it really is — what artifacts (if any) precede implementation, what review
happens, how rework is handled when something doesn't work. It is not a strawman
constructed for contrast.

## 5. Outcome measures

**Primary** (R-400, R-403): rate of contract/code mismatches caught before merge (via the
Structure Gate) versus mismatches that escape and surface later — a follow-up bug report
or a commit re-touching the same seam within 30 days. The Structure Gate only runs on the
Recurspec-workflow task, so this is a directional comparison: the Recurspec-workflow
task's caught-vs-escaped ratio against the escape rate actually observed in the baseline
task over the same follow-up window, not a matched apples-to-apples rate on both sides.
*Data source:* the "caught" side is `check_structure`'s returned `StructureDiagnostic`
list (`src/recurspec/structure_gate.py`) — this already exists as of R-300 and requires no
new instrumentation. The "escaped" side has no automated source on either arm and must be
logged by hand in the decision log as it's found.

**Secondary:**

- R-400: wall-clock time to a first accepted implementation; number of review
  round-trips; count of reverted or redone work. *Data source:* the Recurspec-workflow
  arm can derive elapsed time from the Job Store's `claims.claimed_at` column
  (`src/recurspec/spec_runner/store.py`) against the accepting commit's timestamp; the
  baseline arm has no equivalent store and must be timed by hand.
- R-401: for any procurement/dependency decision made during the task, whether
  Recurspec's Decision Class (`BUY`/`ADOPT`/`WRAP`/`BUILD`/`DEFER`) was later reversed,
  and if so, the cost of the reversal in time or lines changed. Reported as case evidence,
  not a rate — procurement decisions are too infrequent per task for a meaningful count.
  *Data source:* logged by hand in the decision log; Recurspec has no automated tracker
  for a Decision Class being reversed after the fact.
- R-402: for any task that hits at least one failed Candidate attempt, whether a later
  attempt repeats a previously-failed approach. This is measured as a within-Recurspec
  ablation independent of the baseline comparison: rerun the same failing step twice, once
  with Negative Pattern memory available and once with it cleared, and compare the repeat
  rate — the same ablation shape as
  [foundations.md §11](./foundations.md#11-a-repair-memory-ablation-precedent)'s ChatRepair
  precedent, applied to Recurspec's own persistent store instead of a single conversation.
  *Data source:* already instrumented — every revert emits a `negative_pattern` evidence
  event (`record("negative_pattern", ...)` in `src/recurspec/evaluation.py`), and
  `read_negative_patterns`/`count_total_reverts` already read prior-attempt counts back
  out. This ablation requires no new code, only running it.

## 6. Failure definition

The Recurspec-workflow condition is scored `failed-to-help` on a task if it does not reach
an Evaluation-Gate-accepted result within 2× the matched task's completion time, or if the
Contract Tree decomposition is abandoned mid-task in favor of ad-hoc work. A
`failed-to-help` outcome is recorded and reported the same as any other outcome.

## 7. Stopping rule

Data collection continues until either six matched task-pairs across at least two
distinct projects are complete, or six months elapse from the first pair, whichever comes
first. The result is reported at that point regardless of direction. No optional stopping
after seeing a favorable early trend.

## 8. Sample-size rationale

This protocol does not claim a power-analysis-justified sample; six pairs across two
projects is set as the minimum needed to distinguish one unusual task from a repeatable
pattern, matching the ACM SIGSOFT Case Study standard's expectations rather than the
stricter Experiment standard's ([foundations.md §9](./foundations.md#9-pre-registration-precedent-for-effectiveness-claims)).
Findings are reported as descriptive case evidence, not a statistically significant
effect, unless a future dated amendment to this protocol pre-registers a specific
statistical test and the sample size to support it — before that data is collected.

## 9. Analysis method

Descriptive reporting of §5's measures per task pair, plus the decision log R-400's
acceptance criterion already requires (reproducible before/after repositories and
decision logs). Any metric reported that is not listed in §5 must be explicitly labeled
post-hoc, not folded into the primary result.

## 10. Treatment of retries and human intervention

Any manual override of the Evaluation Gate — a human accepting a Candidate the gate would
reject, or rejecting one it would accept — is logged with a reason and counted separately
from gate-driven outcomes. It must not be silently folded into a "Recurspec workflow
succeeded" tally.

## 11. Reporting commitment

The result, including a null or adverse finding, will be published as an update to
[foundations.md](./foundations.md) and reflected in the R-400/R-401/R-402/R-403 status
rows in [ROADMAP.md](../../ROADMAP.md), regardless of whether it favors Recurspec.

## Amendments

None yet. Any change to §2–§10 made after data collection begins must be added here with
a date and reason, per the Registered Reports precedent this protocol follows.
