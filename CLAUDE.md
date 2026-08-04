# RSS — working rules for agents

This repo is the **process source of truth** for the Recursive System Specification
engine. It is documentation + a measurement harness, not a product. Consumer projects
(e.g. `../featherwAIght-rs`) use this process; they do not import this tree.

Read [`docs/README.md`](./docs/README.md) first. Terms are defined in
[`docs/glossary.md`](./docs/glossary.md) — use them precisely.

## Hard rules

1. **One incomplete-work surface.** Every TODO, deferred item, and fog-of-war entry goes
   in [`docs/open-work.md`](./docs/open-work.md). Do not create a second checklist file,
   a phase list inside a design essay, or a readiness sheet. `.scratch/wayfinder-map/`
   owns claimable build tickets only.
2. **No fabricated citations.** Placeholder arXiv IDs and invented paper titles are
   forbidden. If a claim has no primary source, tag the invariant
   `EvidenceStage: Unknown` and say so. Add the source row to
   [`docs/research/foundation.md`](./docs/research/foundation.md) *before* citing it.
3. **Sampled ≠ Proved.** Passing unit tests are `Sampled`. Promotion to `Measured`
   requires the harness; `Proved` requires a solver or algebraic argument. Never promote
   across that line to make a spec look finished.
4. **Archive before removing.** Snapshot into `docs/archive/` and byte-compare before
   deleting anything from the living tree. See [`docs/archive/README.md`](./docs/archive/README.md).
5. **Directory names are kebab-case; the contract file is always `SYSTEM.md`** (ADR-003).
   Note this filesystem is case-insensitive — `RECONCILER/` and `reconciler/` are the
   same directory.
6. **Maker ≠ checker.** An agent that implements a leaf does not authorize its own merge.
   See [`skills/dual-loop/SKILL.md`](./skills/dual-loop/SKILL.md).

## Spec tree

**Resolve before decomposing.** Every node is asked *what will implement this?* before
*what are its parts?* — assign a decision class (BUY / ADOPT / WRAP / BUILD / DEFER) via
[`docs/process/technology-resolution.md`](./docs/process/technology-resolution.md).

- **BUILD carries the burden of proof.** Never hand-roll a solved commodity — auth,
  payments, email, search, telemetry. A BUILD without a recorded justification in §8 is a
  gate failure.
- **Procurement terminates recursion.** A node resolved BUY/ADOPT is a leaf; spec the
  seam, never the vendor's internals. This is what keeps the tree finite.
- **Split where the decision class stops being uniform** — the BUY/BUILD fault line is a
  real interface, because you cannot refactor across a vendor's API.
- Otherwise split by independent interface seam. A node past ~150 lines or 3
  responsibilities is a bloat signal.
- Max depth 4 by default; two-child minimum; no speculative children (fog goes to the
  Wayfinder map).

Terminal nodes carry §6 (test seam), §7 (measurement seam), and §8 (technology
resolution). Invariants use EARS keywords (`[Ubiquitous]`, `[Event-driven]`,
`[State-driven]`, `[Conditional]`) and each carries an `EvidenceStage`.

**Never invent a vendor, version, or price.** The no-fabrication rule that governs
citations governs §8 identically — verify against live docs, or resolve `DEFER`.

Full loop: [`docs/process/decomposition-loop.md`](./docs/process/decomposition-loop.md).
Worked example: [`docs/examples/login-decomposition.md`](./docs/examples/login-decomposition.md).

## Harness

`harness/` implements the Back-Channel B keep/revert gate. Before changing it:

```bash
python -m pytest harness/test_harness.py -q
```

The gate's contract is *refuse rather than guess*: an unparseable measurement, a
self-contradicting instrument, or a metric whose better-direction cannot be resolved must
revert, never pass. Do not add a fallback that substitutes a default metric value — that
manufactures Measured-grade evidence from a failure. See the comparison rules in
`harness/baseline.py`.

## Skills

`skills/` holds the four skills this repo owns: `recursive-spec`, `resolve-stack`,
`reconcile-spec`, `dual-loop`. Install with [`docs/install.md`](./docs/install.md).

**Do not add `sherloc/` or `wayfinder/` copies here.** They are maintained elsewhere and
forks of them were removed for being downgrades; `skills-lock.json` records where the
real ones live.
