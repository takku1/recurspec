# Recursive System Specification (RSS) — Documentation Index

This directory is the **single source of truth** for RSS process design, architecture contracts, research grounding, and incomplete work.

Root-level markdown outside `docs/` is limited to the project [README](../README.md) and [CLAUDE.md](../CLAUDE.md) (agent working rules). Skills live under `skills/`. Runtime harness code lives under `harness/`. Execution frontiers live under `.scratch/wayfinder-map/`.

---

## Map

| Path | Role |
|------|------|
| [glossary.md](./glossary.md) | Ubiquitous language (domain terms) |
| [install.md](./install.md) | Installing the skills + harness for Claude Code |
| [open-work.md](./open-work.md) | **Only** active checklist of incomplete work |
| [research/foundation.md](./research/foundation.md) | Peer-reviewed / primary research grounding |
| [process/decomposition-loop.md](./process/decomposition-loop.md) | **Goal → tree of buildable leaves.** The 5-phase per-node loop and its stopping rules |
| [process/technology-resolution.md](./process/technology-resolution.md) | **Third-party-first gate.** Decision classes, scoring, anti-lock-in, §8 fields |
| [examples/login-decomposition.md](./examples/login-decomposition.md) | Worked example: one flat line → 7 specified nodes |
| [process/dual-backchannel-loop.md](./process/dual-backchannel-loop.md) | 7-stage loop: dual back-channels + branching measurement |
| [process/multi-signal-reconciler.md](./process/multi-signal-reconciler.md) | Structural sensory signals (drift, bloat, seams) |
| [architecture/SYSTEM.md](./architecture/SYSTEM.md) | L0 root contract |
| [architecture/*/SYSTEM.md](./architecture/) | L1 component contracts (recursive leaves) |
| [archive/README.md](./archive/README.md) | Clearance policy |
| [archive/2026-08-02-pre-redesign/](./archive/2026-08-02-pre-redesign/) | **Full pre-redesign snapshot** (reference before any removal) |

---

## Archive-first rule

All pre-redesign root essays, old architecture nodes, readiness checklists, Wayfinder maps, and skill copies live under `archive/2026-08-02-pre-redesign/`. Living docs were rewritten from that reference. **Originals at repo root are not deleted until an explicit removal pass** (see archive README removal gate).

---

## Reading order

**Starting a new project?** Read [process/decomposition-loop.md](./process/decomposition-loop.md) then [examples/login-decomposition.md](./examples/login-decomposition.md), and run `/recursive-spec`. That is the forward path from a goal to buildable leaves.

**Working on RSS itself?**

1. [glossary.md](./glossary.md) — terms
2. [architecture/SYSTEM.md](./architecture/SYSTEM.md) — L0 decomposition
3. [research/foundation.md](./research/foundation.md) — why the design is shaped this way
4. [process/decomposition-loop.md](./process/decomposition-loop.md) — forward loop (spec → leaves)
5. [process/dual-backchannel-loop.md](./process/dual-backchannel-loop.md) — backward loop (reality → blueprint)
6. [open-work.md](./open-work.md) — what is not done yet
7. Claim a leaf on `.scratch/wayfinder-map/MAP.md` and implement against its `SYSTEM.md`

---

## Document hygiene rules

1. **One incomplete-work surface:** all TODOs, fog-of-war, deferred features, and extracted finding/bug work items go in `open-work.md`. Do not maintain parallel checklists (`doc-readiness`, phase lists in design essays, etc.).
2. **Architecture is recursive:** each subsystem is a directory with `SYSTEM.md`. Expand a node only when interface seams justify it; expand research claims only with citable sources (see `research/foundation.md`).
3. **Findings / bugs are temporary:** extract concepts into architecture, process, research, or `open-work`; then delete or archive the source note per [archive/README.md](./archive/README.md).
4. **No fake citations:** placeholder arXiv IDs and invented paper titles are forbidden. Prefer primary sources already listed in research foundation, or mark `EvidenceStage: Unknown`.
