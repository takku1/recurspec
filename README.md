# Recurspec

Recurspec is an evidence-gated system design toolkit for AI-assisted software
engineering. It turns a goal into a finite tree of buildable contracts, resolves
technology before decomposition, evaluates candidate changes against correctness and
measurement gates, and reconciles reality back into the design.

The project ships two public interfaces:

- `recurspec`, a cross-platform Python CLI for contract validation, candidate evaluation,
  and skill setup.
- `/recurspec`, one self-contained agent skill for design, resolution, implementation,
  evaluation, repair, and reconciliation.

Recurspec is alpha software. Its decision logic is tested; full worktree orchestration is
tracked in [ROADMAP.md](./ROADMAP.md).

## Why Recurspec

Flat plans hide radically different work behind equally sized bullets. Recurspec asks
what implements each capability before asking for its parts, assigning one decision:

| Decision | Meaning |
|---|---|
| `BUY` | Use a managed service |
| `ADOPT` | Use an open-source library or framework feature |
| `WRAP` | Build a narrow adapter around `BUY` or `ADOPT` |
| `BUILD` | Implement genuinely differentiating behavior |
| `DEFER` | Stop until research resolves the uncertainty |

`BUY` and `ADOPT` terminate recursion at a procurement seam. `BUILD` and `WRAP` stop
when one module can be implemented in one test-driven session. This makes the contract
tree shallow where the ecosystem has solved the problem and deep only where custom work
is justified.

## Install

```bash
python -m pip install git+https://github.com/takku1/recurspec.git
recurspec skills install
```

For local development:

```bash
git clone https://github.com/takku1/recurspec.git
cd recurspec
python -m pip install -e ".[dev]"
pytest
```

The skill installer targets Claude Code and Codex by default. Verify installation without
writing with `recurspec skills check`.

## Use the agent skill

Start with the single public skill:

```text
/recurspec design a booking system for independent music teachers
```

In Codex, select `recurspec` through `/skills` or invoke `$recurspec`. The skill inspects
the repository state and loads only the internal phase reference it needs.

## Evaluate a candidate

Validate one versioned Contract Node or a complete Contract Tree first:

```bash
recurspec contract check docs/architecture
recurspec contract check docs/architecture --format json
```

Contract Nodes opt in with `<!-- recurspec-contract: 1.0 -->`. The validator checks the
bundled Draft 2020-12 schema, canonical EARS patterns, Evidence Stages, and Atomic Leaf
Sections 6–8. Exit `0` is valid, `1` is invalid, and `2` means the validation instrument
failed.

Each measurable module owns two scripts:

```text
modules/<name>/checks.sh
modules/<name>/measure.sh
```

Evaluate an isolated branch:

```bash
recurspec evaluate <module> candidate/<ticket-id>
```

Exit codes are stable: `0` keep, `1` revert, `2` evaluation error, `3` escalate. Evidence
is appended under `.recurspec/evidence/<module>/log.jsonl`. A kept candidate does not
silently become the reference baseline; after merge, promote it explicitly with
`--record-baseline`.

The gate refuses to guess. Missing or contradictory telemetry, a non-numeric reading, or
an unresolved metric direction reverts the candidate instead of manufacturing evidence.

## Repository map

```text
src/recurspec/             Python package and bundled agent skill
tests/                     Behavioral tests at the package interfaces
modules/evaluation-gate/   Recurspec's own checks and measurement probe
modules/contract-engine/   Contract validation checks and fixture metric
examples/module/           Templates for consumer modules
docs/architecture/         Recursive SYSTEM.md contract tree
docs/process/              Design and evidence-cycle details
docs/research/             Primary-source grounding
CONTEXT.md                 Canonical domain language
ROADMAP.md                 Single incomplete-work registry
```

Start with [the documentation index](./docs/index.md), then read the
[contract-design loop](./docs/process/contract-design.md) and the
[worked identity example](./docs/examples/identity-design.md).

## License

[MIT](./LICENSE)
