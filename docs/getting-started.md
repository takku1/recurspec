# Getting started

## Install the CLI and skill

```bash
python -m pip install git+https://github.com/takku1/recurspec.git
recurspec skills install
recurspec skills check
```

`skills install` copies one self-contained `recurspec` skill to Claude Code and Codex.
Use `--target claude` or `--target codex` to install only one. The installer honors
`CLAUDE_SKILLS_DIR`, `CODEX_SKILLS_DIR`, and `CODEX_HOME`.

Invoke `/recurspec` in Claude Code. In Codex, select it through `/skills` or invoke
`$recurspec`.

## Design a system

Start with a goal:

```text
/recurspec design a booking system for independent music teachers
```

The skill frames capabilities, researches existing solutions, assigns a decision class,
and splits only where ownership or failure modes differ. Terminal nodes include their
test seam, measurement seam, and technology resolution.

## Add an evaluation probe

Before implementation, validate a versioned Contract Node or Contract Tree:

```bash
recurspec contract check docs/architecture
recurspec contract check docs/architecture --format json
```

Add `<!-- recurspec-contract: 1.0 -->` below the title of each opted-in `SYSTEM.md`.
Validation fails closed on unsupported versions, missing required headings, malformed
EARS invariants, missing Evidence Stages, or an empty directory.

For tree composition, declare stable ports as backtick identifiers on Section 3 lines:

```markdown
- **Inputs:** `source_document`
- **Outputs:** `validated_contract`
```

Non-Atomic nodes link children from Section 2. Validation resolves those links inside the
checked tree and verifies that parent inputs and satisfiable sibling outputs supply every
child input and declared parent output.

Copy the templates into a named module:

```bash
mkdir -p modules/checkout
cp examples/module/checks.sh modules/checkout/checks.sh
cp examples/module/measure.sh modules/checkout/measure.sh
```

`checks.sh` provides correctness backpressure. `measure.sh` writes one JSON object to
standard output; diagnostics belong on standard error. Declare metric direction whenever
the name is ambiguous.

Evaluate an isolated candidate:

```bash
recurspec evaluate checkout candidate/OW-42
```

Use `--record-baseline` only after the accepted Candidate is merged. Evidence is local and
append-only under `.recurspec/evidence/`.

The evaluation scripts require a POSIX shell. On Windows, Git Bash is supported and can be
selected explicitly through `RECURSPEC_BASH`.

## Develop Recurspec

```bash
git clone https://github.com/takku1/recurspec.git
cd recurspec
python -m pip install -e ".[dev]"
pytest
ruff check src tests
python -m build
```

See [CONTEXT.md](../CONTEXT.md) for canonical terms and [ROADMAP.md](../ROADMAP.md) for
incomplete work.
