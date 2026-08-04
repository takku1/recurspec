# Installing RSS for Claude Code

RSS ships three skills. They are plain `SKILL.md` files; installing means copying each
into `~/.claude/skills/<name>/`, where Claude Code discovers them at session start.

```bash
for s in recursive-spec reconcile-spec dual-loop; do
  mkdir -p ~/.claude/skills/$s
  cp skills/$s/SKILL.md ~/.claude/skills/$s/SKILL.md
done
```

On Windows the target is `C:\Users\<you>\.claude\skills\`. Start a new session (or
`/clear`) afterwards — the skill list is read at startup.

| Skill | Invocation | Auto-invocable? |
|-------|-----------|-----------------|
| `/recursive-spec` | explicit only | no (`disable-model-invocation: true`) |
| `/reconcile-spec` | explicit or model-chosen | **yes** — it is the drift sensor, so it should fire without being asked |
| `/dual-loop` | explicit only | no |

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

1. Create `docs/architecture/SYSTEM.md` with `/recursive-spec`.
2. Decompose to atomic leaves; each leaf gets §6 (test seam) and §7 (measurement seam).
3. Publish frontier tickets to `.scratch/wayfinder-map/MAP.md` with `/wayfinder`.
4. Copy `harness/measure.sh.template` and `harness/checks.sh.template` to
   `components/<leaf>/` and fill them in.
5. Run leaves through `/dual-loop`; gate merges with `harness/hypothesis_runner.py`.
6. Run `/reconcile-spec` after each merge to feed both back-channels.
