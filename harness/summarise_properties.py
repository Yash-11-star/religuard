"""Turn one version's raw property runs into properties.json and failures.md.

Usage: python3 harness/summarise_properties.py <out dir>   (called by check_version.sh)

Verdict per test: "pass" (passed first time), "flaky" (failed, then passed on the re-run: not a
regression), "fail" (failed both times: a regression).
"""
import json
import re
import sys
from pathlib import Path

out = Path(sys.argv[1])
run1 = json.loads((out / "properties_run1.json").read_text())


def short(nodeid: str) -> str:
    return re.sub(r"[^A-Za-z0-9_-]", "_", nodeid.split("::")[-1])


def prop(nodeid: str) -> str:
    return re.search(r"test_(p\d+)_", nodeid).group(1).upper()


summary = {}
for nodeid, first in run1.items():
    entry = {"property": prop(nodeid), "verdict": "pass", "duration_s": first["duration_s"],
             "message": None, "measured": first["measured"]}
    if first["outcome"] != "passed":
        rerun_file = out / f"rerun_{short(nodeid)}.json"
        rerun = json.loads(rerun_file.read_text()).get(nodeid, {}) if rerun_file.exists() else {}
        entry["first_run"] = {"outcome": first["outcome"], "message": first["message"], "measured": first["measured"]}
        entry["rerun"] = {"outcome": rerun.get("outcome"), "message": rerun.get("message"), "measured": rerun.get("measured")}
        entry["verdict"] = "flaky" if rerun.get("outcome") == "passed" else "fail"
        entry["message"] = first["message"]
        del entry["measured"]
    summary[nodeid.split("::")[-1]] = entry

(out / "properties.json").write_text(json.dumps(summary, indent=2, default=str))

lines = ["# Property failures", ""]
regressions = {k: v for k, v in summary.items() if v["verdict"] == "fail"}
flaky = {k: v for k, v in summary.items() if v["verdict"] == "flaky"}
if not regressions and not flaky:
    lines.append("None: every property passed on the first run.")
for name, v in {**regressions, **flaky}.items():
    kind = "REGRESSION (failed twice)" if v["verdict"] == "fail" else "flaky (failed, then passed on re-run; not a regression)"
    lines += [f"## {v['property']} `{name}`: {kind}", "",
              f"First run: `{v['first_run']['message']}`", "",
              f"Re-run: `{v['rerun']['message']}`" if v["verdict"] == "fail" else "Re-run: passed", "",
              "Measured (first run):", "", "```json",
              json.dumps(v["first_run"]["measured"], indent=2, default=str)[:4000], "```", ""]
    log = out / f"order_log_{short(name)}.txt"
    if log.exists():
        lines += ["Order service log, last 50 lines after the re-run:", "", "```", log.read_text().rstrip(), "```", ""]
(out / "failures.md").write_text("\n".join(lines) + "\n")

for name, v in summary.items():
    print(f"{v['verdict']:5}  {name}")
