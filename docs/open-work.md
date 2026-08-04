# Open Work

**Single registry of incomplete work.** Do not maintain parallel GO/No-GO sheets, phase checklists in process essays, or duplicate fog lists in Wayfinder beyond ticket state.

**Statuses:** `ready` · `blocked` · `deferred` · `research` · `done`  
**Update rule:** When an item completes, mark `done` and prune after the next release note. When something new is incomplete, add a row here — not a new checklist file.

Related: implementation tickets live in [`.scratch/wayfinder-map/MAP.md`](../.scratch/wayfinder-map/MAP.md). This file owns *process/architecture incompleteness*; Wayfinder owns *claimable build tickets*.

---

## Implementation frontier (mirrors Wayfinder)

| ID | Item | Status | Blocked by | Spec |
|----|------|--------|------------|------|
| OW-01 | Spec Engine generator (`src/spec_engine/`) | ready | — | [spec-engine](./architecture/spec-engine/SYSTEM.md) |
| OW-02 | Reconciler auto-expander (`src/reconciler/`) | ready | — | [reconciler](./architecture/reconciler/SYSTEM.md) |
| OW-03 | Wayfinder Connector publisher | blocked | OW-01 | [wayfinder-connector](./architecture/wayfinder-connector/SYSTEM.md) |
| OW-04 | AST Gatekeeper zero-drift checker | blocked | OW-02 | [ast-gatekeeper](./architecture/ast-gatekeeper/SYSTEM.md) |
| OW-05 | Measurement Harness branching runner | blocked | OW-04 | [measurement-harness](./architecture/measurement-harness/SYSTEM.md) |

---

## Process / product incomplete

| ID | Item | Status | Notes |
|----|------|--------|-------|
| OW-10 | Dual-loop skill fully wired to packet templates in `.scratch/handoffs/` | ready | Skill exists under `skills/dual-loop/`; handoff dir convention not dogfooded end-to-end |
| OW-11 | `.measure/` baseline layout + append-only `log.jsonl` convention enforced | done | `harness/baseline.py` reads/writes the convention; `find_baseline` ignores non-trunk branches. No consumer-project baseline yet (see OW-21) |
| OW-12 | Pre-commit / CI: fail on `checks.sh` fail; optional `measure.sh` on changed components | deferred | Local dogfood first |
| OW-13 | Reconciler Signal D (metric drift → Type B Wayfinder ticket) | ready | Harness half done: `hypothesis_runner` emits a `signal_d` event on regression beyond tolerance. Remaining: `/reconcile-spec` consuming it to open the Type B ticket |
| OW-14 | Kitchen Loop trust model (spec surface + unbeatable tests + drift control) as explicit Q(S) reporting | research | See research foundation; no implementation yet |
| OW-15 | Remote GitHub webhook observer for reconcile | deferred | Phase 2+; local hooks enough |
| OW-16 | VS Code interactive tree visualizer | deferred | Phase 3+; markdown/CLI primary |

---

## Doc / hygiene incomplete

| ID | Item | Status | Notes |
|----|------|--------|-------|
| OW-20 | Promote or delete any residual notes under `docs/archive/` | ready | Keep archive empty unless mid-extraction |
| OW-21 | Align consumer project (featherwAIght-rs) paths to kebab-case architecture names | ready | After this docs redesign |
| OW-22 | Skills: replace references to `doc-readiness.md` with `open-work.md` | done | Sole offender was the stale `.agents/skills/` fork, removed with the OW-30 pass. `skills/` already cited `open-work.md` |
| OW-23 | Harness needs its own correctness backpressure wired as a real `checks.sh` | ready | `harness/test_harness.py` exists (31 tests); no `components/harness/checks.sh` yet, so the harness cannot gate itself |

---

## Extracted from findings / bugs (none present)

There is currently **no** `findings/` or `bugs/` tree in this repo. Policy when they appear: **archive first**, then extract — see [archive/README.md](./archive/README.md).

## Removal pass

Executed 2026-08-04, after `git init` made the tree recoverable and each file was
byte-compared against its archive copy. Recover any of it with
`git show <baseline-commit>:<path>`.

| ID | Item | Status | Notes |
|----|------|--------|-------|
| OW-30 | Remove root essays after archive promotion verified | done | 6 essays byte-identical to `archive/…/root/`; `README.md` kept (living, differs from its archived predecessor) |
| OW-31 | Remove SCREAMING_CASE architecture dirs after kebab-case verified | done | `AST_GATEKEEPER`, `MEASUREMENT_HARNESS`, `SPEC_ENGINE`, `WAYFINDER_CONNECTOR` removed. **`RECONCILER` was never a duplicate** — on this case-insensitive filesystem it is the same inode as `reconciler/` |
| OW-32 | Remove `docs/doc-readiness.md` after open-work verified complete | done | Byte-identical to `archive/…/architecture/doc-readiness.md` |

---

## Intentionally out of scope

- Web GUI for non-dev spec editing (terminal + markdown first).
- Treating L4 model-judge scores as merge gates (verification ladder: L1–L3 only for autonomous merge).
