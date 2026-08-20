# Recurspec

Recurspec turns software intent into a finite Contract Tree, resolves what should be
bought or adopted before custom work is decomposed, evaluates isolated Candidates, and
reconciles what implementation teaches back into the design.

Its internal control law is deliberately small:

```text
DISCOVER -> RESOLVE -> EXECUTE -> CHECK -> RECONCILE
```

The mechanisms remain strict: `ROADMAP.md` is the only incomplete-work registry,
Candidates cannot authorize themselves, missing evidence is never guessed, and tests or
measurements are never mislabeled as proof.

Recurspec is alpha software. Its deterministic gates and Candidate lifecycle are tested;
project-level outcome validation remains explicitly unfinished in
[ROADMAP.md](./ROADMAP.md).

## Install

```bash
python -m pip install git+https://github.com/takku1/recurspec.git
recurspec skills install
```

The installer supports Claude Code, Codex, Grok, and Antigravity. Use
`recurspec skills check` for a read-only drift check or `--target NAME` to select one.
The core package needs only Python 3.10+ and `jsonschema`; runtime and Rust adapters are
optional extras.

For development:

```bash
git clone https://github.com/takku1/recurspec.git
cd recurspec
python -m pip install -e ".[dev]"
pytest
```

## Start

Invoke the bundled `recurspec` skill with a goal, or orient any repository directly:

```text
/recurspec design a booking system for independent music teachers
```

```bash
recurspec status .
```

`status` classifies the Contract Tree and prints the next safe route. The common CLI path
is:

```bash
recurspec status .
recurspec check .
recurspec evaluate MODULE candidate/TICKET --worker-state STATE --authorization-id ID
recurspec reconcile plan .
recurspec skills check
```

`check` is read-only. `evaluate` is the explicit authority-bearing gate and returns
`KEEP`, `REVERT`, or `ESCALATE`; a kept Candidate does not silently promote the Best
Known State. Reconciliation produces drafts for review rather than editing contracts.
Narrow compatibility and research commands remain discoverable through
`recurspec --help`.

## Why resolve first

Every Contract Node receives one Decision Class:

| Decision | Meaning |
|---|---|
| `BUY` | Use a managed service |
| `ADOPT` | Use an existing library or framework capability |
| `WRAP` | Own only the Fit Gap behind a narrow adapter |
| `BUILD` | Implement differentiating behavior |
| `DEFER` | Stop at a Research Frontier until uncertainty resolves |

`BUY` and `ADOPT` terminate at the Procurement Seam. `WRAP` and `BUILD` decompose only
until one independently failing seam fits one test-driven session. Coverage Review may
propose missing children or cross-node interfaces, but those proposals begin as
`Unknown` or `Inferred` and require review.

## Repository map

```text
src/recurspec/      installable package and bundled skill
tests/              interface-level behavior tests
modules/            checks and measurement probes
docs/architecture/  recursive Contract Tree
docs/process/       detailed policies loaded when needed
docs/research/      evidence and outcome-study apparatus
CONTEXT.md          canonical domain language
ROADMAP.md          incomplete work only
```

Read the [documentation index](./docs/index.md) or the
[getting-started guide](./docs/getting-started.md). Small or low-risk projects may need
only the validators—or may not need Recurspec at all; see the
[adoption guide](./docs/adoption.md).

## License

[MIT](./LICENSE)
