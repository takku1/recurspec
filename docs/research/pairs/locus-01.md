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

- Recurspec arm started: 2026-08-15 after assignment (not accepted; NEED_CHECKER)
- Recurspec arm work this session: added catalog rule `numerical.one_minus_exp` (`1-exp(x) ≡ -expm1(x)`) plus `one_minus_exp_is_a_catalog_hit` (7 catalog_hit lib tests passed). Horner/expm1/conjugate/hypot were already in RULES_ACCURACY.
- Baseline arm started: contaminated, not validly started (see Post-hoc metrics). Do not run R-ARCH-13 as this pair's baseline arm without a checker decision.
- Accepted implementation: yes. Recurspec arm accepted 2026-08-15 ~01:33 by checker dillon.c.carney@gmail.com (independent of implementor session). Committed `3de12f6` (4 files: `catalog_hit.rs`, `rules/mod.rs`, `rules/records.rs`, `rules/registry.rs` only — Locus main carries ~230 unrelated uncommitted paths from prior work, left untouched). Tests: `cargo test -p locus-engine rules::catalog_hit` (8 passed).

## Post-hoc metrics

List any number reported that is not in the protocol §5 table. Label each `post-hoc`.

- post-hoc: **Baseline-arm contamination discovered 2026-08-15.** Locus's own `ROADMAP.md:32` already lists R-ARCH-13 as `active (2026-08-15: CatalogIndex genome lookup ...; NEED_CHECKER)`, and `.recurspec/handoffs/strategy-R-ARCH-13.md` exists (a Recurspec fanout/strategy artifact, KEEP gate NEED_CHECKER, target `docs/architecture/search/catalog-rules/SYSTEM.md`). The `CatalogIndex`/`CatalogPriority` code that *is* R-ARCH-13's exit gate ("catalog priority index for N2") is the same `catalog_hit.rs` that shipped as scaffolding for the R-U-02 Recurspec-arm tests above. R-ARCH-13 was therefore (a) already substantially implemented before this pair's baseline arm could start, and (b) implemented via Recurspec-style artifacts (Contract Tree doc target, strategy handoff, KEEP gate) rather than the pre-registered "plain workflow" baseline condition. This pair's baseline arm cannot honestly be run as originally assigned — needs a checker decision: void pair locus-01's baseline leg, substitute a fresh unstarted Locus ticket as the baseline arm, or document R-ARCH-13 as a disqualified/contaminated observation.
