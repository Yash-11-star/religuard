"""Remove every mention of the study and the P1-P10 checks from an agent workspace.

Usage: python3 harness/scrub_agent_view.py <workspace> (called by make_agent_view.sh).
Only docs, comments, and the Makefile/CI targets change; no code behaviour. Every replacement must match exactly once, or the script stops.
"""
import re
import sys
from pathlib import Path

ws = Path(sys.argv[1])


def sub(path, old, new):
    p = ws / path
    s = p.read_text()
    n = s.count(old)
    if n != 1:
        sys.exit(f"{path}: expected 1 match, found {n}: {old[:60]!r}")
    p.write_text(s.replace(old, new))


# README: neutral title, drop the intro and the four project-tracking sections.
p = ws / "README.md"
s = p.read_text()
s = "# Online store\n\nThree FastAPI services (order, payment, inventory) with Postgres and Toxiproxy, run with docker-compose.\n\n" + s[s.index("## Running locally"):]
p.write_text(s)
sub("README.md", "| used by the property checks to inject faults |", "| fault injection (latency, outages) |")
sub("README.md", "| Order → Postgres (for P10) |", "| Order → Postgres |")
sub("README.md", " This is the service the coding agents change.", "")
sub("README.md", " (P9 checks `PENDING` is empty)", "")
sub("README.md", "**Reliability behaviour of Version 0** (constants at the top of `services/order/app.py`; these are what P1–P10 check):",
    "**Reliability behaviour** (constants at the top of `services/order/app.py`):")
sub("README.md", "Charge rows (count these for duplicate-charge checks P5, P6)", "Charge rows")
sub("README.md", "`missing_key`). Used by P4 |", "`missing_key`) |")
sub("README.md", "then it switches back to normal. Used by P4, P8 |", "then it switches back to normal |")
sub("README.md", " (P8 compares these before/after)", "")
for line in ("properties/                           reliability property checks P1-P10\n",
             "changes/                              the 8 change-request prompts\n",
             "harness/                              runs agents through the change sequence\n",
             "religuard/                            evidence builder + repair loop\n",
             "results/                              JSON results per agent / run / change\n",
             "analysis/                             RQ1-RQ3 scripts and figures\n",
             "report/                               midpoint and final report sources\n"):
    sub("README.md", line, "")

# Makefile: drop the properties target.
sub("Makefile", " test-services properties\n", " test-services\n")
sub("Makefile", "\nproperties: venv  ## Run the reliability property checks P1-P10 against the running stack\n"
    "\t$(VENV)/bin/pytest -v --durations=0 --durations-min=0.1 properties\n", "")

# CI: drop the property step and the ticket comment.
sub(".github/workflows/ci.yml", "\n      - name: Property checks\n        run: make properties\n", "")
sub(".github/workflows/ci.yml", "# Each later ticket adds its own test step (#5 functional tests, #6-#9 property checks).\n", "")

# Compose comments.
sub("docker-compose.yml", "# control API (used by the property checks)", "# control API (fault injection)")
sub("docker-compose.yml", "so the property checks can inject faults.", "so faults can be injected in testing.")

# .gitignore: course documents and experiment output.
sub(".gitignore", "# Course documents kept local only (the proposal contains student IDs)\n"
    "/Project_Proposal_Template__CS59300_ASE__Vedant_and_Yash.pdf\n"
    "/Midpoint Project Report Instructions.pdf\n\n", "")
sub(".gitignore", "# Raw experiment output (summaries in results/ are committed)\nresults/raw/\n\n", "")

# Docstrings.
sub("services/order/app.py", "Version 0 is written to satisfy every reliability property (P1-P10):", "Reliability behaviour:")
sub("services/payment/app.py", "Records every charge, deduplicates by Idempotency-Key, and exposes admin endpoints that the\n"
    "reliability property checks use to count charges/attempts (P4, P5, P6, P8) and to force\n"
    "HTTP 503s or declines, which Toxiproxy cannot produce at the TCP level.",
    "Records every charge, deduplicates by Idempotency-Key, and exposes admin endpoints to count\n"
    "charges/attempts and to force HTTP 503s or declines, which Toxiproxy cannot produce at the TCP level.")
sub("services/payment/app.py", "whatever the outcome. Used to count attempts (P4).", "whatever the outcome. Used to count attempts.")
sub("services/inventory/app.py", "The admin endpoints\nlet the property checks see stock levels before and after a fault (P8).",
    "The admin endpoints\nshow stock levels and reservations.")
sub("tests/services/test_order.py", "These cover the checkout API itself. The fault-injection reliability properties (P1-P10) live in\n"
    "properties/ (#6-#9).\n", "These cover the checkout API itself.\n")

left = []
for f in ws.rglob("*"):
    if f.is_file() and ".git" not in f.parts:
        for i, line in enumerate(f.read_text(errors="ignore").splitlines(), 1):
            if re.search(r"\bP(10|[1-9])\b|propert|harness|agent|religuard/|study|experiment|course|proposal|midpoint|CS ?59300|Purdue|Yash|Vedant", line, re.I):
                left.append(f"{f.relative_to(ws)}:{i}: {line.strip()}")
print("\n".join(left) or "no references left")
