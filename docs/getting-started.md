# Getting started

## Install the CLI and skill

```bash
python -m pip install git+https://github.com/takku1/recurspec.git
python -m pip install "recurspec[runtime]"  # optional: Anthropic Messages adapter
recurspec skills install
recurspec skills check
```

`skills install` copies one self-contained `recurspec` skill to Claude Code, Codex, Grok,
and Antigravity. Use `--target claude|codex|grok|antigravity` to select one. Antigravity
also accepts the compatibility aliases `agy` and `gemini`; `AGY_SKILLS_DIR` overrides
the [documented user-scope directory](https://docs.cloud.google.com/application-design-center/docs/design-deploy-antigravity-cli),
`~/.gemini/config/skills`. `GEMINI_HOME` is retained as a Recurspec compatibility
override, not represented as an Antigravity environment variable.

Invoke `/recurspec` in Claude Code or Grok. In Codex, select it through `/skills` or
invoke `$recurspec`.

## Design a system

The skill's first action is the CLI, not a guess from existing docs:

```bash
recurspec status .
recurspec status . --format json
```

`status` classifies the Contract Tree as `missing`, `not_recurspec`, `invalid`, or
`valid`. A `SYSTEM.md` file without `<!-- recurspec-contract: 1.0 -->` is
`not_recurspec` — source material, not a finished Recurspec design. `FEATURE_GAPS.md`
and similar incomplete-work files do not replace `ROADMAP.md`. Declared §7 probe
scripts that are not on disk set `route` to `repair`. A second tree at
`.recurspec/contracts` is listed under `extra_trees`.

A numbered list of work is not one design pass. Split it first:

```bash
recurspec fanout --item "missing probes" --item "extra contract trees" --write
```

Each item gets its own `.recurspec/handoffs/strategy-*.md`. Design and implement one
handoff at a time.

Then start with a goal:

```text
/recurspec design a booking system for independent music teachers
```

The skill frames capabilities, performs a bounded Coverage Review, researches existing
solutions, assigns a Decision Class, and splits only where ownership or failure modes
differ. Coverage findings begin as `Unknown` or `Inferred`; they never mutate the tree
automatically. Terminal nodes include their test seam, measurement seam, and Technology
Resolution.

Run the common read-only checks together:

```bash
recurspec check .
recurspec check . --only contract,evidence,structure,resolution,frontier
```

Narrow command families remain available for compatibility and focused diagnostics.

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
recurspec evaluate checkout candidate/R-200 \
  --worker-state .recurspec/worker-authorizations.json --authorization-id R-200
```

The authorization record must have been emitted after a successful independent Worker
Pool CHECK. Use `--record-baseline` only
after the accepted Candidate is merged. Evidence is local and append-only under
`.recurspec/evidence/`.

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
