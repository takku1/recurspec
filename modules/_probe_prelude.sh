#!/usr/bin/env bash
# Shared probe preamble. Every bundled checks.sh/measure.sh sources this so the
# repository root, import path, and interpreter are resolved one way, in one place.
# Four variants had already drifted apart across 18 files - two probes never
# exported PYTHONPATH at all, and two skipped the Windows `pwd -W` guard (R-701).

# BASH_SOURCE[1] is the sourcing probe; [0] is this file, used only if run directly.
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[1]:-${BASH_SOURCE[0]}}")/../.." && (pwd -W 2>/dev/null || pwd))"
cd "${REPO_ROOT}"

# Python splits PYTHONPATH on ';' on Windows and ':' elsewhere. Joining with ':'
# unconditionally turned an existing PYTHONPATH into one bogus entry, so the probe
# could not import the package under test and failed for the wrong reason.
case "${OSTYPE:-}" in
  msys* | cygwin* | win32*) _RECURSPEC_PATH_SEP=";" ;;
  *) _RECURSPEC_PATH_SEP=":" ;;
esac
export PYTHONPATH="${REPO_ROOT}/src${PYTHONPATH:+${_RECURSPEC_PATH_SEP}${PYTHONPATH}}"

# Some systems only ship python3, not a bare "python" alias; a bundled probe must
# not silently assume the maintainer's own dev environment shape.
PYTHON="${RECURSPEC_PYTHON:-$(command -v python3 2>/dev/null || command -v python 2>/dev/null || true)}"
if [ -z "${PYTHON}" ]; then
  echo "no python3 or python interpreter found on PATH" >&2
  exit 127
fi
