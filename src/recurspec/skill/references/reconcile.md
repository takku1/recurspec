# Contract Reconciliation

Detect Structural Feedback (implementation shape and the Contract Tree disagree) with
`recurspec structure check`, turn it into reviewable draft actions with
`recurspec reconcile plan`, and defer Empirical Feedback (measured behavior and a
Contract Node's claims disagree) to the Evaluation Gate. The reconciler is
**draft-only**: it never edits `SYSTEM.md` files itself. Every action is a proposal an
Architect applies or rejects.

## Structural signals and their draft actions

- **Uncontracted source** (`structure.public.uncontracted` /
  `structure.source.uncontracted`): a public symbol or file has no parent Contract
  Node. Action: `draft_leaf` — a generated `SYSTEM.md` draft (Evidence Stage `Unknown`,
  no Decision Class) under `docs/architecture/drafts/...`, for Architect review before
  it is linked into the tree.
- **Uncontracted test surface** (`structure.test.uncontracted`): Action:
  `test_seam_review` — flag for Architect review; no file is generated.
- **Ambiguous or missing declarations** (`structure.implementation.ambiguous`,
  `structure.implementation.missing`, `structure.test_surface.missing`): Action:
  `contract_repair_review` — the existing `SYSTEM.md` Section 6 declaration disagrees
  with the filesystem; flag for repair.
- **Structural bloat** (a Contract Node exceeds the line limit or declares more than 3
  separable Responsibilities): Action: `split_review` — flag the node as a decomposition
  candidate.

## Empirical signal

`recurspec reconcile plan --evidence-log <path>` counts `signal_d` events (metric
regressions and telemetry contradictions already recorded by the Evaluation Gate) as
`deferred_empirical_events` in the plan output. Empirical Feedback is never auto-applied
here — it stays in the Evaluation Gate's own evidence log
(`.recurspec/evidence/<module>/log.jsonl`) until an Architect resolves it, tracked as a
Research Frontier in `ROADMAP.md` if it needs its own ticket. Do not invent a parallel
tracker for it.

## Applying a plan

1. Run `recurspec reconcile plan <repository> --format json` and read every action.
2. For each `draft_leaf`, review the generated draft, then link it into its intended
   parent's Section 2 yourself (or discard it) — the CLI never writes it into the tree.
3. For `test_seam_review`, `contract_repair_review`, and `split_review`, make the
   corresponding `SYSTEM.md` edit by hand; there is no generated content to review.
4. Re-run `recurspec structure check` to confirm the drift is resolved.
5. If implementation files changed, run `recurspec modules check <repository>` with
   those paths as `--changed-file` so the touched modules' probes run.

## Verification Gate

Ensure zero un-specced files remain (`recurspec structure check` passes), every
invariant carries a current `EvidenceStage` tag, and
`recurspec reconcile plan` reports no remaining actions.
