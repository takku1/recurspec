# Recurspec code review

Review date: 2026-08-13

This is an evidence snapshot, not a second readiness list. Remediation status lives only
in [ROADMAP.md](../ROADMAP.md), under R-600 through R-608.

## Outcome

The package is well tested on its current happy paths: all 154 tests pass, Ruff reports
no violations, and both the source archive and wheel build successfully. The review also
reproduced five high-priority edge cases that can either authorize an invalid merge,
bypass a core invariant, or make the documented evaluation workflow unusable.

Recommended fix order:

1. R-600: protect the Evaluation Gate's probes from Candidate changes.
2. R-601: make checker approval and maker/checker separation authoritative.
3. R-602: fail closed on invalid telemetry and ambiguous evidence.
4. R-603: reject hollow or disconnected Contract Trees.
5. R-604: make the documented authorization-state path compatible with clean-worktree enforcement.
6. R-605 and R-606: align the bundled skill and measurement probes with the implemented CLI.
7. R-607 and R-608: harden pin and path validation.

## High priority

### H1. A Candidate can replace its own gate probes and merge itself (R-600)

The evaluator constructs `modules/<name>/checks.sh` and `measure.sh`, then runs both with
the Candidate worktree as `cwd` ([evaluation.py](../src/recurspec/evaluation.py#L208)). It
only checks for uncommitted probe mutations after evaluation
([evaluation.py](../src/recurspec/evaluation.py#L441)); committed Candidate changes to the
probe files are trusted.

Reproduction: a baseline was created with a failing `checks.sh`. Its Candidate committed
a passing replacement, changed product state from `safe` to `broken`, and emitted a
favorable metric. `evaluate_isolated_candidate()` returned `KEEP` (`0`), fast-forwarded
the baseline, and left the weakened probe merged.

Impact: correctness backpressure is not an independent gate when the code being judged
also controls the judge. An accidental or hostile Candidate can delete tests, weaken
checks, or manufacture measurement output.

Recommended correction: execute probe definitions from the trusted baseline while
pointing them at the Candidate worktree, or refuse Candidate probe changes unless a
separate instrument-change authorization explicitly covers their exact object IDs.

### H2. Worker Pool state does not prove independent approval (R-601)

There are two independently reproduced bypasses in
[workers.py](../src/recurspec/spec_runner/workers.py#L147):

- A CHECK returning `{"approved": false, "reason": "tests failed"}` still produces
  `WorkerResult(outcome="ok")` and a merge authorization. The runtime response has no
  typed approval verdict; any within-budget response is treated as success.
- CHECK can run before any producer exists. If that worker later runs FRAME for the same
  node, `merge_authorization()` returns an authorization whose maker and checker are the
  same identity. The identity check occurs only before the runtime call and is not
  revalidated when state is committed ([workers.py](../src/recurspec/spec_runner/workers.py#L184)).

Concurrent producer/checker calls have the same time-of-check/time-of-use risk. A later
producer can also overwrite the maker after a check has been recorded. In addition, an
injected runtime exception escapes instead of returning the documented `tool_error`.

Impact: the central maker/checker invariant can be bypassed, and a checker rejection can
be represented as authorization.

Recommended correction: model an atomic per-node lifecycle. Require a successful
producer before CHECK, keep that maker immutable for the reviewed Candidate, require a
typed positive checker verdict, revalidate maker != checker while committing state, and
translate runtime failures to `tool_error` without persisting authorization.

### H3. Invalid telemetry and damaged evidence fail open (R-602)

`_numeric()` accepts every Python float without checking `math.isfinite()`
([metrics.py](../src/recurspec/metrics.py#L118)). Python's JSON decoder accepts `NaN` by
default. The review reproduced this sequence:

```text
{"metric":"latency_ms","value":NaN}
telemetry contradiction: None
comparison: NEUTRAL
```

The resulting reason was `regressed nan% but within 20.0% tolerance`, so an unusable
reading can authorize KEEP. A payload containing only `{"value": 1}` is likewise
accepted, assigned `unknown_metric`, and treated as the first neutral measurement
([evaluation.py](../src/recurspec/evaluation.py#L292)). Non-finite CLI tolerance values
are not rejected either.

Separately, malformed evidence lines are silently skipped
([metrics.py](../src/recurspec/metrics.py#L75)). When the only baseline event was corrupt,
`find_baseline()` returned no baseline and a 10x latency regression became a neutral
first measurement.

Impact: Recurspec can manufacture `Measured` evidence or accept a regression precisely
when its evidence is ambiguous, contrary to its fail-closed interface rule.

Recommended correction: require finite numeric values, non-empty metric names, valid
directions/tiers, and finite non-negative gate configuration. Distinguish a recoverable
truncated final append from corruption of a prior evidence event; the latter must return
an instrument error rather than erase the baseline.

### H4. Hollow and disconnected Contract Trees validate successfully (R-603)

Atomic-leaf requirements depend on the exact `Atomic leaf.` prefix. A Contract Node that
does not declare that prefix and has no child links is treated as a non-leaf, so only
Sections 1–5 are required ([contract.py](../src/recurspec/contract.py#L233)). A reproduced
L0 document containing `Decomposition pending.` passed both single-file and directory
validation without Sections 6–8 or a Technology Resolution.

Directory validation also checks links that are present but never requires every
discovered node to be linked. Adding a valid, unlinked L1 node to the valid-tree fixture
still returned `valid=True`; `build_tree_index()` then produced two nodes with
`parent_id=None` ([contract.py](../src/recurspec/contract.py#L423)). Multiple parents are
also overwritten rather than diagnosed at index construction.

Impact: the machine-checkable result may not be a tree, and a terminal responsibility
can evade the resolution and Atomic Leaf requirements.

Recommended correction: require exactly one `SYSTEM.md` L0 root, require every other
node to be reachable from it exactly once, reject multi-parent nodes, and require every
non-leaf to declare at least one valid child.

### H5. The documented Worker Pool state path makes evaluation refuse to start (R-604)

The documented command uses `.recurspec/worker-authorizations.json`. Worker Pool writes
that file before evaluation, but the repository ignore rules cover evidence logs and
handoffs, not authorization state ([.gitignore](../.gitignore#L11)). The evaluator then
requires an entirely clean baseline before doing any work
([evaluation.py](../src/recurspec/evaluation.py#L386)).

Reproduction: persisting a valid maker/checker authorization at the documented path made
`git status --porcelain` report `?? .recurspec/`; evaluation then raised `baseline
worktree must be clean before candidate evaluation`.

Impact: a correctly generated prerequisite prevents the documented CLI workflow from
running in a repository that has not independently added the state path to `.gitignore`.
Evidence logs can cause the same problem on the next evaluation when they are not ignored.

Recommended correction: store runtime authorization/evidence outside the worktree, add
an explicit initialization step that installs scoped ignore rules, or have the cleanliness
check safely exclude only Recurspec-owned runtime state.

## Medium priority

### M1. Bundled skill references contradict the shipped CLI and vocabulary (R-605)

The public skill's reconciliation reference tells an agent to call `graphgraph`,
`code-review-graph`, and Sherloc, and to automatically edit contracts
([reconcile.md](../src/recurspec/skill/references/reconcile.md)). Those integrations are
not package dependencies or CLI interfaces; the implemented reconciler is deliberately
draft-only. The design and resolution references also direct deferred work to a
`.scratch/wayfinder-map/MAP.md` list and repeatedly use `Type B`, even though
[CONTEXT.md](../CONTEXT.md) defines `Research Frontier` as the canonical term and
[AGENTS.md](../AGENTS.md) requires `ROADMAP.md` to be the sole incomplete-work surface.

Impact: the installed agent interface can request unavailable tools, mutate contracts
beyond the implemented safety seam, and create the parallel work list forbidden by the
repository rules.

Recommended correction: rewrite the phase references around `recurspec structure check`,
`recurspec reconcile plan`, Research Frontiers, reviewable drafts, and R-nnn roadmap
entries. Add a repository test for banned domain terms and unavailable tool names.

### M2. Documented measurement surfaces are missing or partially ignored (R-606)

The Job Store and Worker Pool contracts name `modules/job-store/{checks,measure}.sh` and
`modules/worker-pool/{checks,measure}.sh`, but neither directory exists. The Contract
Engine measurement script emits two top-level JSON objects
([measure.sh](../modules/contract-engine/measure.sh#L19)), while `parse_measurement()`
selects only the last recoverable object. The probe reproduced two emitted metrics with
only `valid_tree_fixture_acceptance_rate` selected; `valid_fixture_acceptance_rate` was
silently discarded.

Impact: documented module evaluation cannot run for two completed modules, and one
declared Contract Engine metric never reaches baseline comparison or promotion.

Recommended correction: add the missing scripts and wrap multiple readings in the
supported `{"metrics": [...]}` envelope. Add an end-to-end test that feeds every bundled
`measure.sh` output through `parse_measurement()` and asserts the expected metric set.

### M3. "Exact" dependency inventories accept floating constraints (R-607)

`load_dependency_inventory()` accepts any non-empty version string, and the audit only
checks string equality ([technology_resolver.py](../src/recurspec/technology_resolver.py#L92)).
An inventory and Contract Node that both say `latest`, `>=1`, or `*` therefore pass the
staleness comparison even though the public contract calls these exact versions.

Impact: Technology Resolution can report a reproducible pin while retaining an
unbounded or floating dependency choice.

Recommended correction: validate exact-version syntax for the selected dependency
ecosystem, or require inventory entries to carry an explicit ecosystem plus an
authoritatively resolved exact version.

## Low priority

### L1. CLI path arguments can escape their declared seams (R-608)

`module` is interpolated into script and evidence paths without rejecting absolute paths
or `..` segments ([evaluation.py](../src/recurspec/evaluation.py#L145)). Structure and
stack root overrides similarly accept paths outside the repository, after which some
`relative_to(root)` calls can raise uncaught exceptions.

Impact: this is primarily a local hardening and diagnostics issue because the CLI user
supplies the arguments, but mistakes can execute the wrong probe or write evidence
outside `.recurspec/evidence/<module>`.

Recommended correction: accept only a single safe module-name segment; resolve all
repository-relative options, prove containment before I/O, and return stable exit `2`
instrument diagnostics for invalid paths.

## Verification record

| Check | Result | Evidence Stage |
|---|---|---|
| `pytest` | 154 passed | Sampled |
| `ruff check src tests` | Passed | Sampled |
| `python -m build` | Source archive and wheel built | Sampled |
| Targeted edge-case probes | H1–H5 and M2 reproduced | Observed |

This was a single-checker review. The findings and priorities remain ready for owner or
independent maintainer review; they are not formal proof.
