"""pytest plugin: record what each property check measured, without changing properties/.

Load with `-p record_measurements` (harness/ on PYTHONPATH); set PROPERTIES_DIR=<the properties/
folder> and MEASUREMENTS_OUT=<file.json>.
It wraps the helpers the checks call (checkout, charges, attempts, stock, pending_orders) and
writes, per test: outcome, duration, assertion message, and every value those helpers returned.
"""
import functools
import json
import os
import sys

import pytest

_results: dict[str, dict] = {}
_current: list[str] = []


def _summarise(name, value):
    if name == "checkout":
        resp, elapsed = value
        try:
            body = resp.json()
        except ValueError:
            body = resp.text[:200]
        return {"status": resp.status_code, "elapsed_s": round(elapsed, 3), "body": body}
    if name in ("charges", "pending_orders"):
        return {"count": len(value), "rows": value}
    return value


def _wrap(module, name):
    original = getattr(module, name)

    @functools.wraps(original)
    def wrapper(*args, **kwargs):
        value = original(*args, **kwargs)
        if _current:
            _results[_current[0]]["measured"].append({"call": name, **({"kwargs": kwargs} if kwargs else {}),
                                                      "result": _summarise(name, value)})
        return value

    setattr(module, name, wrapper)


def pytest_configure(config):
    # properties/ has no __init__.py, so its conftest imports `helpers` as a top-level module.
    sys.path.insert(0, os.environ["PROPERTIES_DIR"])
    import helpers
    for name in ("checkout", "charges", "attempts", "stock", "pending_orders"):
        _wrap(helpers, name)


def pytest_runtest_setup(item):
    _results.setdefault(item.nodeid, {"outcome": None, "duration_s": 0.0, "message": None, "measured": []})
    _current[:] = [item.nodeid]


def pytest_runtest_logreport(report):
    entry = _results.setdefault(report.nodeid, {"outcome": None, "duration_s": 0.0, "message": None, "measured": []})
    if report.when == "call" or report.failed:
        entry["outcome"] = report.outcome if report.when == "call" else f"{report.when} {report.outcome}"
        entry["duration_s"] = round(entry["duration_s"] + report.duration, 3)
        if report.failed:
            crash = getattr(report.longrepr, "reprcrash", None)
            entry["message"] = crash.message if crash else str(report.longrepr)[-2000:]


def pytest_unconfigure(config):
    out = os.environ.get("MEASUREMENTS_OUT")
    if out:
        with open(out, "w") as f:
            json.dump(_results, f, indent=2, default=str)
