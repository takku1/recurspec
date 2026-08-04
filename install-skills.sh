#!/usr/bin/env bash
# Install this repo's skills into ~/.claude/skills.
#
# Also the recovery path: mattpocock/skills ships its own, much smaller,
# `recursive-spec` and `reconcile-spec`. Running /setup-matt-pocock-skills
# overwrites ours with those. Re-run this to restore.
#
#   ./install-skills.sh            install/update
#   ./install-skills.sh --check    report drift without writing
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEST="${CLAUDE_SKILLS_DIR:-$HOME/.claude/skills}"
SKILLS=(recursive-spec resolve-stack reconcile-spec dual-loop)
CHECK=0
[[ "${1:-}" == "--check" ]] && CHECK=1

[[ -d "$DEST" ]] || { [[ $CHECK -eq 1 ]] && { echo "no skills dir: $DEST"; exit 1; }; mkdir -p "$DEST"; }

drift=0
for s in "${SKILLS[@]}"; do
  src="$REPO/skills/$s/SKILL.md"
  dst="$DEST/$s/SKILL.md"
  [[ -f "$src" ]] || { printf '  %-16s MISSING IN REPO\n' "$s"; drift=1; continue; }

  if [[ ! -f "$dst" ]]; then
    status="not installed"
  elif cmp -s "$src" "$dst"; then
    printf '  %-16s up to date\n' "$s"; continue
  else
    status="DIFFERS (installed $(wc -l < "$dst")L vs repo $(wc -l < "$src")L)"
  fi

  drift=1
  if [[ $CHECK -eq 1 ]]; then
    printf '  %-16s %s\n' "$s" "$status"
  else
    mkdir -p "$DEST/$s" && cp "$src" "$dst"
    printf '  %-16s installed (%s)\n' "$s" "$status"
  fi
done

if [[ $CHECK -eq 1 ]]; then
  [[ $drift -eq 0 ]] && echo "all in sync" || { echo; echo "run ./install-skills.sh to sync"; exit 1; }
else
  echo
  echo "Done. Start a new session (or /clear) — skills load at startup."
fi
