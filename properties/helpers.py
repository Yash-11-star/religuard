"""Helpers for the reliability property checks (#6): fault injection and state inspection.

Faults go in through Toxiproxy (latency, outages, dropped responses) and the Payment fault switch
(HTTP 503s and declines, which Toxiproxy cannot produce). State is read through the services'
/admin endpoints. Everything here is undone by reset_all(), which the `stack` fixture runs before
and after every check.
"""
import os
import time
import uuid

import httpx

ORDER = os.environ.get("ORDER_URL", "http://localhost:8000")
PAYMENT = os.environ.get("PAYMENT_URL", "http://localhost:8001")
INVENTORY = os.environ.get("INVENTORY_URL", "http://localhost:8002")
TOXIPROXY = os.environ.get("TOXIPROXY_URL", "http://localhost:8474")

# Order first, so its background finalizers stop before Payment and Inventory are cleared.
SERVICES = (ORDER, PAYMENT, INVENTORY)
PROXIES = ("payment", "inventory", "order_db")

# Long enough that a checkout is never cut off by the client: the checks measure the service's
# own answer time, so the client must outwait any hang it is checking for.
CLIENT_TIMEOUT = 30.0

http = httpx.Client(timeout=CLIENT_TIMEOUT)


# ---------------------------------------------------------------- stack lifecycle


def wait_healthy(timeout: float = 60.0) -> None:
    """Block until Toxiproxy and all three services answer, or fail with what is still down."""
    checks = {"toxiproxy": f"{TOXIPROXY}/version", **{base: f"{base}/health" for base in SERVICES}}
    end = time.monotonic() + timeout
    down = list(checks)
    while time.monotonic() < end:
        down = [name for name, url in checks.items() if not _ok(url)]
        if not down:
            return
        time.sleep(0.5)
    raise RuntimeError(f"stack not healthy after {timeout:.0f}s: {', '.join(down)} (run `make up`)")


def _ok(url: str) -> bool:
    try:
        return http.get(url, timeout=2).status_code == 200
    except httpx.HTTPError:
        return False


def clear_faults() -> None:
    """Remove all toxics, re-enable all proxies, and turn off the Payment fault switch; keep data."""
    http.post(f"{TOXIPROXY}/reset").raise_for_status()
    set_payment_fault("none", 0)


def reset_all() -> None:
    """Remove all toxics, re-enable all proxies, clear every service's data and fault switch."""
    http.post(f"{TOXIPROXY}/reset").raise_for_status()
    for base in SERVICES:
        http.post(f"{base}/admin/reset").raise_for_status()


# ---------------------------------------------------------------- faults


def add_toxic(proxy: str, type: str, attributes: dict, stream: str = "downstream", name: str | None = None) -> dict:
    """Add a Toxiproxy toxic to `proxy`. `stream` is downstream (server -> Order) or upstream."""
    resp = http.post(
        f"{TOXIPROXY}/proxies/{proxy}/toxics",
        json={"name": name or f"{type}_{stream}", "type": type, "stream": stream, "attributes": attributes},
    )
    resp.raise_for_status()
    return resp.json()


def remove_toxic(proxy: str, name: str) -> None:
    http.delete(f"{TOXIPROXY}/proxies/{proxy}/toxics/{name}").raise_for_status()


def _set_enabled(proxy: str, enabled: bool) -> None:
    http.post(f"{TOXIPROXY}/proxies/{proxy}", json={"enabled": enabled}).raise_for_status()


def disable_proxy(proxy: str) -> None:
    """Take a dependency down: Toxiproxy closes the listener, so Order gets connection refused."""
    _set_enabled(proxy, False)


def enable_proxy(proxy: str) -> None:
    _set_enabled(proxy, True)


def set_payment_fault(mode: str, count: int) -> None:
    """Make the next `count` /charge calls fail: mode "503", "decline", or "none" to clear."""
    http.post(f"{PAYMENT}/admin/fault", json={"mode": mode, "count": count}).raise_for_status()


# ---------------------------------------------------------------- checkout and state


def checkout(sku: str = "SKU-1", qty: int = 1, amount: str = "10.00", key: str | None = None):
    """POST /checkout and time it. Returns (response, elapsed seconds)."""
    t0 = time.monotonic()
    resp = http.post(
        f"{ORDER}/checkout",
        json={"sku": sku, "qty": qty, "amount": amount},
        headers={"Idempotency-Key": key or uuid.uuid4().hex},
    )
    return resp, time.monotonic() - t0


def charges(order_id: str) -> list[dict]:
    """Charge rows Payment stored for this order (duplicates show up as extra rows)."""
    return http.get(f"{PAYMENT}/admin/charges", params={"order_id": order_id}).json()


def payment_requests(order_id: str) -> list[dict]:
    """Every /charge call Payment received for this order, with its outcome."""
    return http.get(f"{PAYMENT}/admin/requests", params={"order_id": order_id}).json()["requests"]


def attempts(order_id: str) -> int:
    """How many /charge calls Payment received for this order."""
    return http.get(f"{PAYMENT}/admin/requests", params={"order_id": order_id}).json()["attempts"]


def stock(sku: str = "SKU-1") -> dict:
    """{"sku", "available", "reserved"} from Inventory."""
    return http.get(f"{INVENTORY}/admin/stock/{sku}").json()


def pending_orders() -> list[dict]:
    return http.get(f"{ORDER}/admin/orders", params={"status": "PENDING"}).json()


def wait_until(predicate, timeout: float, interval: float = 0.1):
    """Poll `predicate` until it returns something truthy or `timeout` passes; returns its last value."""
    end = time.monotonic() + timeout
    while True:
        value = predicate()
        if value or time.monotonic() >= end:
            return value
        time.sleep(interval)
