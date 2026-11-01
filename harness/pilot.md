# Pilot run (#12): Claude Code, run 1, changes 01 and 02

Exactly what was run, in order, so the pilot can be reproduced. Results are in
`results/pilot/claude-code/run1/`.

## Environment

| | |
|---|---|
| Host | macOS (Apple Silicon), Docker via colima 2 CPU / 4 GB (`colima start --cpu 2 --memory 4`) |
| Agent | Claude Code 2.1.309 (Homebrew cask `claude-code`), model `claude-sonnet-5-5` |
| App under test | `origin/6-property-checks` @ `7061ad2` (Version 0 services + property checks) |
| Prompts | `origin/11-change-prompts` @ `a6eda51` |
| Checks | `properties/` from `origin/6-property-checks`, pytest 8.3.4, httpx 0.28.1 (`make venv`) |

## 1. Build the agent's working copy

```bash
git fetch origin
git checkout -b 12-pilot-run origin/6-property-checks
make down
harness/make_agent_view.sh origin/6-property-checks ../agent-claude-run1
```

`make_agent_view.sh` exports the ref with `git archive`, deletes `properties/ harness/ results/
religuard/ analysis/ report/ changes/`, runs `scrub_agent_view.py`, and commits the result as
`v0` in a fresh repository with a fixed author and date. The same ref always gives tree
`38c8efe5` and commit `076f2a7`.

### Scrub: every edit

Only mentions of P1–P10, the property checks, the study, agents, and ReliGuard are removed. No
code changes; comments that describe behaviour (timeouts, retries, idempotency keys) stay.

| File | Edit |
|---|---|
| README.md | Title `# ReliGuard` + project intro (study description) replaced by `# Online store` and one sentence describing the three services |
| README.md | Sections "Tracking the work", "Order of work", "Midpoint plan", "All tickets" deleted (everything above "Running locally") |
| README.md | Port table: "used by the property checks to inject faults" → "fault injection (latency, outages)"; "Order → Postgres (for P10)" → "Order → Postgres" |
| README.md | Order API: removed "This is the service the coding agents change." and "(P9 checks `PENDING` is empty)"; "Reliability behaviour of Version 0 (…; these are what P1–P10 check)" → "Reliability behaviour (constants at the top of `services/order/app.py`)" |
| README.md | Payment API: removed "(count these for duplicate-charge checks P5, P6)", "Used by P4", "Used by P4, P8" |
| README.md | Inventory API: removed "(P8 compares these before/after)" |
| README.md | Repository layout: removed the lines for `properties/ changes/ harness/ religuard/ results/ analysis/ report/` |
| Makefile | `properties` target and its `.PHONY` entry removed |
| .github/workflows/ci.yml | "Property checks" step removed; comment "Each later ticket adds its own test step (#5 …, #6-#9 property checks)" removed |
| docker-compose.yml | "control API (used by the property checks)" → "control API (fault injection)"; "so the property checks can inject faults" → "so faults can be injected in testing" |
| .gitignore | Removed the "Course documents … proposal" block (two PDF names) and the "Raw experiment output … results/raw/" block |
| services/order/app.py | Docstring "Version 0 is written to satisfy every reliability property (P1-P10):" → "Reliability behaviour:" (the list below it is unchanged) |
| services/payment/app.py | Docstring: "admin endpoints that the reliability property checks use to count charges/attempts (P4, P5, P6, P8) and to force …" → "admin endpoints to count charges/attempts and to force …"; table comment "Used to count attempts (P4)." → "Used to count attempts." |
| services/inventory/app.py | Docstring "The admin endpoints let the property checks see stock levels before and after a fault (P8)." → "The admin endpoints show stock levels and reservations." |
| tests/services/test_order.py | Docstring: removed "The fault-injection reliability properties (P1-P10) live in properties/ (#6-#9)." |

After the edits the script searches every file for
`P1..P10, propert, harness, agent, religuard/, study, experiment, course, proposal, midpoint,
CS 59300, Purdue, Yash, Vedant` and prints any hit; there were none.

### Baseline on the scrubbed copy (before any agent run)

```bash
harness/check_version.sh ../agent-claude-run1 results/pilot/claude-code/run1/baseline_v0
```

Service tests 30/30 passed; property checks 12/12 passed (`results/pilot/claude-code/run1/baseline_v0/`).

## 2. For each change (01, then 02 on top of the agent's result)

```bash
harness/run_agent.sh   ../agent-claude-run1 NN results/pilot/claude-code/run1/change_NN
harness/check_version.sh ../agent-claude-run1 results/pilot/claude-code/run1/change_NN
```

`run_agent.sh`:

1. Builds the prompt from `origin/11-change-prompts:changes/preamble.txt` + `change_NN.txt`
   (saved as `prompt.txt`) and records `claude --version`.
2. Runs, exactly once, in the workspace, with a clean environment:
   ```bash
   env -i HOME="$HOME" USER="$USER" PATH=/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin TERM=xterm-256color \
     claude -p "$prompt" --model claude-sonnet-5-5 --permission-mode bypassPermissions \
       --output-format json --max-turns 80 > transcript_NN.json
   ```
   No follow-up messages.
3. `make down` (in case the agent left the stack running), `git add -A`,
   `git commit -m "change NN (agent)"`, saves `git diff HEAD~1` → `diff.patch` and
   `git diff --stat HEAD~1` → `diffstat.txt`.

`check_version.sh`:

1. Copies `properties/` from `origin/6-property-checks` into a temp folder outside the workspace.
2. In the workspace: `make down`, `make up` (the agent's compose file), `make test-services`
   → `functional.txt` (the agent's own tests).
3. Runs the whole property suite with the `harness/record_measurements.py` pytest plugin, which
   wraps the helpers (`checkout`, `charges`, `attempts`, `stock`, `pending_orders`) and records
   every value they return, without changing `properties/` → `properties_run1.json`.
4. Re-runs each failing test once on its own → `rerun_<test>.json`, then saves the last 50 lines
   of the order service log → `order_log_<test>.txt`. A test that fails both times is a
   regression; one that passes on the re-run is "flaky".
5. `summarise_properties.py` writes `properties.json` (verdict + measured values per test) and
   `failures.md`; then `make down`.

## Results

See `results/pilot/claude-code/run1/summary.md`.

## Harness problems found in the pilot

- `--output-format json` saves only the agent's final message and totals (turns, cost, duration),
  not the turn-by-turn tool calls. For the study, use `--output-format stream-json --verbose` so
  the transcript shows what the agent read and ran.
- P8 [503] and P4 assert "checkout failed" before checking their property, so a change that makes
  checkout succeed through the fault (change 02) fails them for the wrong reason (P8) or skips the
  measurement (P4). See the caveats in `summary.md`.
- The property checks never exercise dependencies an agent adds (change 01's Notification service).

## Deviations from the ticket text

- `transcript_NN.json` and the prompt are written to `results/…`, not into the workspace:
  otherwise `git add -A` would commit change 01's transcript into the agent's repo, where it could
  read it during change 02.
- The agent runs with `env -i` because the shell this harness ran in (the Claude desktop app)
  exports ~30 `CLAUDE_*` variables that change a child agent's behaviour.
- The scrub goes beyond the four README sections listed in the ticket (agreed with Vedant): the
  intro, comments, docstrings, and `.gitignore` also named the checks or the study.
