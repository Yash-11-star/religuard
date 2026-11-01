"""Evaluate the running stack: reset it, run the functional tests and property checks, save JSON.

    python3 harness/evaluate.py --out results/v0 --runs 5

Each run writes <out>/run-<n>.json, and <out>/summary.json records which tests passed in every
run. A reliability regression is a property that passed on the previous version and fails on the
next one, so the agent harness (#17) compares these files version to version.

Uses only the standard library plus the test venv (make venv); per-test outcomes come from
pytest's built-in JUnit XML report.
"""
import argparse
import json
import subprocess
import sys
import tempfile
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PYTEST = ROOT / ".venv" / "bin" / "pytest"
SUITES = {"functional": "tests/functional", "properties": "properties"}


def git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True).stdout.strip()


def run_suite(path: str) -> dict:
    """Run one pytest suite; return per-test outcomes keyed by test id (file::name[param])."""
    with tempfile.TemporaryDirectory() as tmp:
        xml = Path(tmp) / "report.xml"
        t0 = time.monotonic()
        subprocess.run([str(PYTEST), "-q", "-p", "no:cacheprovider", f"--junitxml={xml}", path],
                       cwd=ROOT, capture_output=True, text=True)
        elapsed = time.monotonic() - t0
        tests = {}
        if xml.exists():
            for case in ET.parse(xml).iter("testcase"):
                test_id = f"{case.get('classname', '').split('.')[-1]}::{case.get('name')}"
                outcome, message = "passed", None
                for tag in ("failure", "error", "skipped"):
                    node = case.find(tag)
                    if node is not None:
                        outcome = {"failure": "failed"}.get(tag, tag)
                        message = (node.get("message") or "")[:500]
                tests[test_id] = {"outcome": outcome, "duration_s": round(float(case.get("time", 0)), 3),
                                  "message": message}
    counts = {o: sum(t["outcome"] == o for t in tests.values()) for o in ("passed", "failed", "error", "skipped")}
    return {"path": path, **counts, "total": len(tests), "duration_s": round(elapsed, 2), "tests": tests}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", required=True, help="directory for run-<n>.json and summary.json")
    parser.add_argument("--runs", type=int, default=1)
    args = parser.parse_args()
    out = ROOT / args.out
    out.mkdir(parents=True, exist_ok=True)

    meta = {"commit": git("rev-parse", "HEAD"), "dirty": bool(git("status", "--porcelain", "--", "services"))}
    runs = []
    for n in range(1, args.runs + 1):
        subprocess.run(["make", "-s", "reset"], cwd=ROOT, check=True, capture_output=True)
        run = {**meta, "run": n, "started_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
               "suites": {name: run_suite(path) for name, path in SUITES.items()}}
        (out / f"run-{n}.json").write_text(json.dumps(run, indent=2) + "\n")
        runs.append(run)
        print(f"run {n}: " + ", ".join(f"{name} {s['passed']}/{s['total']}" for name, s in run["suites"].items()))

    summary = {**meta, "runs": len(runs), "suites": {}}
    for name in SUITES:
        ids = sorted({t for r in runs for t in r["suites"][name]["tests"]})
        always = [t for t in ids if all(r["suites"][name]["tests"].get(t, {}).get("outcome") == "passed" for r in runs)]
        summary["suites"][name] = {"total": len(ids), "passed_every_run": len(always),
                                   "not_always_passing": [t for t in ids if t not in always]}
    (out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    clean = all(not s["not_always_passing"] for s in summary["suites"].values())
    print(f"{'all green' if clean else 'NOT all green'} over {len(runs)} run(s); wrote {args.out}/")
    return 0 if clean else 1


if __name__ == "__main__":
    sys.exit(main())
