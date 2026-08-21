# Case-study decision log (R-400–R-403)

Use one copy of this file per matched task pair. Fill it **before** either task starts, except the outcome rows. Do not invent numbers. If a field is unknown, write `unknown` — never a default metric.

This is apparatus, not results. Recurspec's own repository is excluded from the task population ([evaluation-protocol.md](../evaluation-protocol.md) §2).

## Pre-registration binding

- Protocol version / date: 2026-08-14
- Pair id: `locus-01`
- Project (not recurspec itself): `C:/Users/dcarn/aiprojects/locus`
- Assignment method (coin flip / first-picked) and result: coin flip via secrets.randbelow(2); Recurspec arm = R-U-02 Accuracy-directed rewrite rules (Horner, expm1, conjugate as catalog rules); Baseline arm = R-ARCH-13 Catalog priority index for N2
- A-priori time estimate for each task (set before either starts): 4h each (one session)

## Tasks

| Arm | Task name | Scope estimate | Condition |
|---|---|---|---|
| Recurspec | R-U-02 Accuracy-directed rewrite rules (Horner, expm1, conjugate as catalog rules) | 4h each (one session) | Contract Tree + Decision Class + Evaluation Gate |
| Baseline | R-ARCH-13 Catalog priority index for N2 | 4h each (one session) | Project's existing workflow, described as it is |

## Baseline workflow (as it really is)

Locus ROADMAP + docs/open-work.md alias; implement on main; cargo test / cargo check as review; rework is more commits on main. No isolated Recurspec evaluate.

## Outcomes (fill only as observed)

| Measure | Recurspec arm | Baseline arm | Source |
|---|---|---|---|
| Wall-clock to first accepted implementation | ~27 min (2026-08-15 01:06 first edit -> 01:33 accept) | unknown | mtime of `records.rs` -> checker accept, this session |
| Review round-trips | unknown | unknown | |
| Reverted or redone work | 0 reverted; `rules/registry.rs` restructured under `e6002d7` (+368 lines) around the accepted rule | n/a | `git show --stat e6002d7` |
| Structure-Gate diagnostics caught before merge | unknown | n/a | |
| Escaped mismatches within 30 days | 1 observed, window still open (opened 2026-08-15, closes 2026-09-14) | n/a (baseline arm disqualified) | `git log` in locus: `e6002d7` (2026-08-20) re-touches the R-U-02 seam |
| Decision Class later reversed? cost? | unknown | unknown | |
| Repeated a previously-failed approach? | unknown | n/a | |
| Failed-to-help? (2× time or tree abandoned) | unknown | unknown | |

## Manual Evaluation Gate overrides

| When | Gate would have | Human did | Reason |
|---|---|---|---|

## Arm start (observed, not a-priori)

- Recurspec arm started: 2026-08-15 after assignment (not accepted; NEED_CHECKER)
- Recurspec arm work this session: added catalog rule `numerical.one_minus_exp` (`1-exp(x) ≡ -expm1(x)`) plus `one_minus_exp_is_a_catalog_hit` (7 catalog_hit lib tests passed). Horner/expm1/conjugate/hypot were already in RULES_ACCURACY.
- Baseline arm started: contaminated, not validly started (see Post-hoc metrics).
- Baseline arm disposition (2026-08-15): **disqualified**. R-ARCH-13 is not a valid
  no-Recurspec control. Do not run it as this pair's baseline arm. Substitute a
  fresh, uncontaminated Locus ticket in a new pair log if a second baseline
  observation is needed.
- Accepted implementation: yes. Recurspec arm accepted 2026-08-15 ~01:33 by checker dillon.c.carney@gmail.com (independent of implementor session). Committed `3de12f6` (4 files: `catalog_hit.rs`, `rules/mod.rs`, `rules/records.rs`, `rules/registry.rs` only — Locus main carries ~230 unrelated uncommitted paths from prior work, left untouched). Tests: `cargo test -p locus-engine rules::catalog_hit` (8 passed).

## Post-hoc metrics

List any number reported that is not in the protocol §5 table. Label each `post-hoc`.

- post-hoc: **Baseline-arm contamination discovered 2026-08-15.** Locus's own `ROADMAP.md:32` already lists R-ARCH-13 as `active (2026-08-15: CatalogIndex genome lookup ...; NEED_CHECKER)`, and `.recurspec/handoffs/strategy-R-ARCH-13.md` exists (a Recurspec fanout/strategy artifact, KEEP gate NEED_CHECKER, target `docs/architecture/search/catalog-rules/SYSTEM.md`). The `CatalogIndex`/`CatalogPriority` code that *is* R-ARCH-13's exit gate ("catalog priority index for N2") is the same `catalog_hit.rs` that shipped as scaffolding for the R-U-02 Recurspec-arm tests above. R-ARCH-13 was therefore (a) already substantially implemented before this pair's baseline arm could start, and (b) implemented via Recurspec-style artifacts (Contract Tree doc target, strategy handoff, KEEP gate) rather than the pre-registered "plain workflow" baseline condition. This pair's baseline arm cannot honestly be run as originally assigned — needs a checker decision: void pair locus-01's baseline leg, substitute a fresh unstarted Locus ticket as the baseline arm, or document R-ARCH-13 as a disqualified/contaminated observation.

- post-hoc: **Escape observation 2026-08-21 (30-day window still open).** Locus commit
  `e6002d7` (2026-08-20, day 5 of the window) re-touches this pair's Recurspec-arm seam —
  `rules/catalog_hit.rs` (±20 lines) and `rules/registry.rs` (+368 lines) — and its message
  records regression **R-REG-01**: after R-ARCH-19 moved `optimize()` onto coordinate-directed
  selection, rules that were still present in the catalog and still compiled were never handed
  to the e-graph and silently stopped firing (23 tests failed; `cargo test --workspace` exited
  101). That is a contract/code mismatch of exactly the kind §5 counts as *escaped*: R-U-02's
  accepted test `one_minus_exp_is_a_catalog_hit` asserted catalog membership, which remained
  true while the behavioral guarantee did not. The repair added **R-REG-02**, a registry test
  asserting every `ALL_RULES` entry is reachable from some family and vice versa — the
  structural invariant that would have caught it. The Structure Gate did not catch this before
  merge; it was found by a full-workspace test run five days later. Counted as 1 escape so far;
  the window does not close until 2026-09-14 and this cell must be re-checked then.
- Verification 2026-08-21: `cargo test -p locus-engine rules::catalog_hit` → 8 passed. The
  R-U-02 rule still fires after the R-REG-01 repair; the accepted work was not reverted.

