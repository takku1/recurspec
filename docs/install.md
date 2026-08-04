# Installing RSS for Claude Code

RSS ships four skills. They are plain `SKILL.md` files; installing means copying each
into `~/.claude/skills/<name>/`, where Claude Code discovers them at session start.

```bash
./install-skills.sh            # install or update all four
./install-skills.sh --check    # report drift without writing (exits non-zero on drift)
```

Start a new session (or `/clear`) afterwards — the skill list is read at startup.
Override the target with `CLAUDE_SKILLS_DIR`; it defaults to `~/.claude/skills`.

### ⚠ Name collision with mattpocock/skills

`recursive-spec` and `reconcile-spec` here are **derived from** the versions in
[mattpocock/skills](https://github.com/mattpocock/skills) and share their names. Running
`/setup-matt-pocock-skills` silently overwrites both with the smaller upstream versions,
losing the decomposition loop and the technology-resolution gate.

`./install-skills.sh --check` detects this; `./install-skills.sh` restores. Worth running
after any bulk skill install.

| Skill | Role | Invocation | Auto-invocable? |
|-------|------|-----------|-----------------|
| `/recursive-spec` | Goal → tree of buildable leaves | explicit only | no (`disable-model-invocation: true`) |
| `/resolve-stack` | "What actually implements this?" on one node | explicit or model-chosen | **yes** — it should fire when someone is about to build something that already exists |
| `/reconcile-spec` | Back-Channel A drift | explicit or model-chosen | **yes** — it is the drift sensor |
| `/dual-loop` | Outer/Inner agent separation | explicit only | no |

### Typical first run

```
/recursive-spec    a booking site for music teachers
```

It will frame the goal, survey what already exists for each capability, resolve each node
to BUY/ADOPT/WRAP/BUILD, split where those classes differ, and stop at procurement
boundaries — leaving you a tree of `SYSTEM.md` files whose leaves each carry a real stack.
Then `/resolve-stack` on any node you want re-examined.

## What this repo deliberately does not install

`/sherloc` and `/wayfinder` are **maintained outside this repo**. Earlier versions of RSS
carried forked copies under `skills/`; those forks were strict downgrades and have been
removed.

| Skill | Real source | Why not from here |
|-------|-------------|-------------------|
| `sherloc` | `C:\Users\dcarn\aiprojects\sherloc\` (source of truth per global `CLAUDE.md`; ships `references/formalisms.md`, `references/full_mode.md`) | The fork was a condensed single file and dropped the reference material |
| `wayfinder` | installed via `setup-matt-pocock-skills` | The installed skill is tracker-aware (native blocking edges, claiming protocol, fog-of-war graduation); the fork was ~a third of its length |

Installing the forks would have overwritten the richer skills in place. Nothing was lost
by dropping them: the RSS-specific content they carried — Type A/B frontier semantics and
the metric-drift → Type B ticket rule — lives in
[`glossary.md`](./glossary.md), [`architecture/wayfinder-connector/SYSTEM.md`](./architecture/wayfinder-connector/SYSTEM.md) §4,
and the Signal D section of `/reconcile-spec`.

`skills-lock.json` records both the owned skills and these external dependencies.

## Harness dependencies

The measurement harness needs Python 3.9+ and a POSIX shell on `PATH` (`bash`; Git Bash
is fine on Windows). `pytest` is needed only to run the harness's own tests.

```bash
python -m pytest harness/test_harness.py -q
```

## Using RSS in a consumer project

RSS is a *process* repo — keep it as the source of truth and point consumer projects at
it rather than copying the tree. In the consumer repo:

1. Run `/recursive-spec` on the goal. It creates `docs/architecture/SYSTEM.md` and
   recurses: frame → research → resolve → split-or-stop → specify.
2. Terminal leaves arrive with §6 (test seam), §7 (measurement seam), and §8 (technology
   resolution). Procured nodes stop at the seam; you do not spec the vendor's internals.
3. `DEFER` nodes become Type B tickets on `.scratch/wayfinder-map/MAP.md` — clear them
   with `/research` or `/prototype`, then resume decomposition of that subtree.
4. Copy `harness/measure.sh.template` and `harness/checks.sh.template` to
   `components/<leaf>/` and fill them in.
5. Run leaves through `/dual-loop`; gate merges with `harness/hypothesis_runner.py`.
6. Run `/reconcile-spec` after each merge to feed both back-channels.

Check the **BUILD ratio** after step 1. If most terminal nodes are BUILD, the research
phase was skipped — re-run `/resolve-stack` on the ones that look like commodities.
