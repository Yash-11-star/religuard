#!/usr/bin/env bash
# Run the agent's own tests and the hidden property checks against one agent version.
#
#   harness/check_version.sh <agent workspace> <out dir> [properties ref]
#
# Writes to <out dir>: functional.txt, properties.json (verdict per property, with measured values),
# failures.md, properties_run1.json, and per failing test rerun_<test>.json and order_log_<test>.txt
# (last 50 lines of the order service log after the re-run). properties/ is copied from the ref
# into a temp folder outside the workspace, so the agent never sees it.
set -uo pipefail
set -f  # test ids contain [brackets]; never glob them

ws=$(cd "${1:?usage: check_version.sh <workspace> <out dir> [ref]}" && pwd)
out=$(mkdir -p "${2:?usage}" && cd "$2" && pwd)
ref=${3:-origin/6-property-checks}
here=$(cd "$(dirname "$0")" && pwd)
repo=$(cd "$here/.." && pwd)
pytest="$repo/.venv/bin/pytest"

props=$(mktemp -d)
trap 'rm -rf "$props"' EXIT
git -C "$repo" archive "$ref" properties | tar -x -C "$props"

cd "$ws"
make down >/dev/null 2>&1
make up > "$out/make_up.txt" 2>&1 || { echo "make up failed, see $out/make_up.txt"; make down >/dev/null 2>&1; exit 1; }

# The agent's own tests (whatever tests/ now contains).
make test-services > "$out/functional.txt" 2>&1
tail -1 "$out/functional.txt"

run_props() {  # $1 = output json, rest = pytest selection
  local json=$1; shift
  (cd "$props" && PYTHONPATH="$here" PROPERTIES_DIR="$props/properties" MEASUREMENTS_OUT="$json" \
    "$pytest" -q -p no:cacheprovider -p record_measurements "$@" 2>&1 | tail -3)
}

run_props "$out/properties_run1.json" properties
failed=$(python3 -I -c 'import json,sys; print(" ".join(k for k,v in json.load(open(sys.argv[1])).items() if v["outcome"]!="passed"))' "$out/properties_run1.json")

# A failing property is re-run once on its own; it is a regression only if it fails both times.
for t in $failed; do
  name=$(echo "$t" | sed 's/.*:://; s/[^A-Za-z0-9_-]/_/g')
  echo "re-running once: $name"
  run_props "$out/rerun_$name.json" "$t"
  docker compose logs --no-color --tail=50 order > "$out/order_log_$name.txt" 2>&1
done

python3 -I "$here/summarise_properties.py" "$out"
make down >/dev/null 2>&1
