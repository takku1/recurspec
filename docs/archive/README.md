# Archive & Clearance Policy

## Purpose

`findings/`, `bugs/`, ad-hoc scratch notes, and obsolete design essays are **temporary capture surfaces**. Concepts must be promoted into the living docs tree; the capture surface is cleared **only after** a dated archive snapshot exists and promotion is verified.

## Procedure (strict order)

1. **Archive first** — copy sources into `docs/archive/YYYY-MM-DD-<label>/` (full tree, not excerpts).
2. **Use archive as reference** — redesign living docs under `docs/` (glossary, open-work, research, process, architecture).
3. **Verify** — every durable concept has a home; every incomplete item is in `open-work.md` or Wayfinder.
4. **Remove originals only after step 3** — delete or slim root orphans / old folders with an explicit pass (do not delete mid-redesign).

## Snapshot: `2026-08-02-pre-redesign/`

Full pre-redesign reference (24 files). **Do not delete this snapshot.**

| Subfolder | Contents |
|-----------|----------|
| `root/` | `README.md`, `CONTEXT.md`, `ACADEMIC_RESEARCH_BLUEPRINT.md`, `DUAL_BACKCHANNEL_MEASUREMENT_LOOP.md`, `MULTI_SIGNAL_SPEC_ENGINE.md`, `MISSING_ARCHITECTURAL_PILLARS.md`, `SKILL_DRAFT.md` |
| `architecture/` | `doc-readiness.md` + full `architecture/**/SYSTEM.md` tree (SCREAMING_CASE dirs) |
| `scratch-wayfinder/` | `.scratch/wayfinder-map/*` frontier tickets + MAP |
| `skills-draft/` | `skills/*` and `.agents/skills/*` SKILL.md copies |

## Target homes after extraction

| Content type | Promote to |
|--------------|------------|
| Interface / invariant / decomposition | `docs/architecture/**/SYSTEM.md` |
| Loop stage / signal / agent role | `docs/process/*` |
| Citable principle or paper | `docs/research/foundation.md` |
| Incomplete work / checklists | `docs/open-work.md` |
| Claimable implementation | `.scratch/wayfinder-map/` |
| Domain term | `docs/glossary.md` |

## Clearance of findings / bugs (when present)

1. Archive the folder under a dated snapshot.
2. Extract concepts into architecture / process / research / open-work.
3. Delete the live `findings/` or `bugs/` tree only after extraction.
4. Never leave parallel permanent checklists inside findings notes.

## Forbidden

- Deleting sources before a dated archive exists.
- Parallel checklists that duplicate `open-work.md` after redesign settles.
- Invented academic references.

## Removal gate — executed 2026-08-04

- [x] Living docs cover all archive concepts needed for day-to-day work
- [x] `open-work.md` holds all incomplete items formerly in doc-readiness / dual-loop phases / Wayfinder fog
- [x] Cross-links updated (README, docs README, skills, `skills-lock.json`)
- [x] Deleted: 6 root essays, `docs/doc-readiness.md`, 4 SCREAMING_CASE architecture dirs, the stale `.agents/skills/` fork

Each file was byte-compared against its snapshot copy before deletion, and the repo was
placed under git first, so every removal is recoverable with
`git show <baseline-commit>:<path>`.

**`RECONCILER/` was not a duplicate.** On this case-insensitive filesystem it resolves to
the same inode as `reconciler/`; deleting it would have destroyed the living contract.
Verify with `stat -c '%i %n'` before assuming a SCREAMING_CASE path is a separate copy.

Skill forks (`skills/sherloc`, `skills/wayfinder`) were also removed — see
[`../install.md`](../install.md) for where the maintained versions live.
