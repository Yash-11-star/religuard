#!/usr/bin/env bash
# Run Claude Code headless on one change request, exactly once, then commit what it did.
#
#   harness/run_agent.sh <agent workspace> <NN> <out dir> [prompts ref] [model]
#
# The prompt is changes/preamble.txt + changes/change_NN.txt from the prompts ref, unedited.
# The agent runs with a clean environment (env -i: only HOME, USER, PATH, TERM), so nothing from
# the calling session changes its behaviour. Its transcript is written to <out dir>, outside the
# workspace, so later changes cannot read it.
set -euo pipefail

ws=$(cd "${1:?usage: run_agent.sh <workspace> <NN> <out dir> [prompts ref] [model]}" && pwd)
nn=${2:?usage}
out=$(mkdir -p "${3:?usage}" && cd "$3" && pwd)
ref=${4:-origin/11-change-prompts}
model=${5:-claude-sonnet-5-5}
here=$(cd "$(dirname "$0")" && pwd)

prompt=$(git -C "$here/.." show "$ref:changes/preamble.txt" "$ref:changes/change_$nn.txt")
printf '%s\n' "$prompt" > "$out/prompt.txt"
claude --version > "$out/claude_version.txt"

cd "$ws"
start=$(date +%s)
env -i HOME="$HOME" USER="$USER" PATH="/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin" TERM=xterm-256color \
  claude -p "$prompt" --model "$model" --permission-mode bypassPermissions \
    --output-format json --max-turns 80 > "$out/transcript_$nn.json" 2> "$out/agent_stderr.txt" || true
echo "agent wall time: $(( $(date +%s) - start ))s" | tee "$out/agent_walltime.txt"

# Whatever the agent left running is stopped before we commit and check.
make down >/dev/null 2>&1 || true
git add -A
git commit -q -m "change $nn (agent)" --allow-empty
git diff HEAD~1 > "$out/diff.patch"
git diff --stat HEAD~1 > "$out/diffstat.txt"
tail -1 "$out/diffstat.txt"
