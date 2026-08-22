# Recurspec contributor rules

Recurspec is an installable Python package plus one bundled agent skill. Read
[CONTEXT.md](./CONTEXT.md) before changing domain terms and [docs/index.md](./docs/index.md)
before changing contracts.

## Invariants

1. Keep every deferred task and incomplete feature in [ROADMAP.md](./ROADMAP.md). Do not
   create parallel readiness lists.
2. Do not fabricate citations, vendors, versions, features, or prices. Verify unstable
   facts against primary sources or classify the decision `DEFER`.
3. Passing tests are `Sampled`; runtime measurements are `Measured`; only formal proof is
   `Proved`.
4. Resolve technology before decomposing. A `BUY` or `ADOPT` node terminates at its seam.
5. Use kebab-case directory names. Architecture contracts are always named `SYSTEM.md`.
6. Maker and checker must differ. An implementor cannot authorize its own merge.
7. The package and skill expose one public name: `recurspec`. Phase references are
   internal implementation details.

## Verification

Run the complete local gate before publishing:

```bash
python -m pytest
ruff check src tests
recurspec contract check docs/architecture
recurspec contract check docs/examples/log-archive
recurspec structure check .
recurspec stack check .
recurspec reconcile plan .
recurspec contract evidence docs/architecture
recurspec check .
python -m build
```

The evaluation interface must refuse ambiguous or contradictory evidence. Never replace a
missing metric with a default numeric value.

## Layout

- `src/recurspec/` — package implementation and bundled skill
- `tests/` — interface-level behavior tests
- `modules/` — checks and measurement probes
- `docs/architecture/` — recursive contract tree
- `docs/process/` — process details
- `ROADMAP.md` — sole incomplete-work surface
