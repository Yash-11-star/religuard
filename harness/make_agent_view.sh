#!/usr/bin/env bash
# Build the agent's working copy: Version 0 with every trace of the study and the checks removed.
#
#   harness/make_agent_view.sh <git ref> <new workspace dir>
#   e.g. harness/make_agent_view.sh origin/6-property-checks ../agent-claude-run1
#
# Same ref in -> byte-identical tree and the same "v0" commit hash out (fixed author and date),
# so every run starts from the identical copy. See harness/pilot.md for the list of edits.
set -euo pipefail

ref=${1:?usage: make_agent_view.sh <git ref> <new workspace dir>}
dest=${2:?usage: make_agent_view.sh <git ref> <new workspace dir>}
here=$(cd "$(dirname "$0")" && pwd)

[ -e "$dest" ] && { echo "$dest already exists; remove it first" >&2; exit 1; }
mkdir -p "$dest"
git -C "$here/.." archive "$ref" | tar -x -C "$dest"

# The checks, the harness, results, and project docs never reach the agent.
rm -rf "$dest"/{properties,harness,results,religuard,analysis,report,changes}

# README sections, Makefile target, CI step, and comments/docstrings that mention them.
python3 -I "$here/scrub_agent_view.py" "$dest"

# Fresh history, so nothing can be found in git log.
cd "$dest"
git init -q -b main
git add -A
GIT_AUTHOR_NAME=harness GIT_AUTHOR_EMAIL=harness@localhost GIT_AUTHOR_DATE=2026-01-01T00:00:00Z \
GIT_COMMITTER_NAME=harness GIT_COMMITTER_EMAIL=harness@localhost GIT_COMMITTER_DATE=2026-01-01T00:00:00Z \
  git commit -q -m v0
echo "v0 tree $(git rev-parse HEAD^{tree})  commit $(git rev-parse --short HEAD)  in $dest"
