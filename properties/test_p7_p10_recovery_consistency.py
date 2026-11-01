"""P7-P10 (#9): recovery after an outage, consistent stock, no stuck orders, bounded DB latency."""
import time

import pytest

from helpers import (
    ORDER, add_toxic, checkout, clear_faults, disable_proxy, enable_proxy, http, pending_orders,
    set_payment_fault, stock, wait_until,
)

MAX_RECOVERY_SECONDS = 10.0     # P7: a checkout succeeds within this after Payment is restored
MAX_RELEASE_SECONDS = 5.0       # P8: reserved stock is back within this after the failed checkout
MAX_PENDING_SECONDS = 5.0       # P9: no PENDING orders within this after faults are removed
DB_LATENCY_MS = 1500            # P10: injected latency on the orders DB
MAX_CHECKOUT_SECONDS = 3.0      # P10: checkout must answer within this


def test_p7_payment_restored_checkouts_recover_within_10s():
    """P7: After Payment is down and then comes back, a new checkout succeeds within 10 s."""
    disable_proxy("payment")
    down, _ = checkout()
    assert down.status_code >= 500, f"expected an error while Payment is down, got {down.status_code}"

    enable_proxy("payment")
    restored_at = time.monotonic()
    last = None
    while time.monotonic() - restored_at <= MAX_RECOVERY_SECONDS:
        last, _ = checkout()
        if last.status_code == 200:
            break
        time.sleep(0.2)
    recovery = time.monotonic() - restored_at
    assert last.status_code == 200, f"no successful checkout {recovery:.1f}s after restore: {last.text}"
    assert recovery <= MAX_RECOVERY_SECONDS


@pytest.mark.parametrize("fault", ["decline", "payment_down"])
def test_p8_failed_payment_releases_reservation(fault):
    """P8: When Payment declines or is down, the stock reserved for that checkout is given back."""
    before = stock()
    if fault == "decline":
        set_payment_fault("decline", 10)
    else:
        # Down for the whole checkout, so no retry policy can get the payment through.
        disable_proxy("payment")
    resp, _ = checkout(qty=3)
    assert resp.status_code >= 400, f"expected the checkout to fail, got {resp.status_code}: {resp.text}"

    wait_until(lambda: stock() == before, MAX_RELEASE_SECONDS)
    after = stock()
    assert after == before, f"stock before {before}, after {after}"


def run_fault_scenarios() -> None:
    """One checkout under each kind of fault the other checks use."""
    scenarios = [
        lambda: add_toxic("payment", "latency", {"latency": 5000}),
        lambda: add_toxic("inventory", "latency", {"latency": 5000}),
        lambda: disable_proxy("payment"),
        lambda: disable_proxy("inventory"),
        lambda: set_payment_fault("503", 10),
        lambda: add_toxic("payment", "timeout", {"timeout": 0}),
        lambda: add_toxic("order_db", "latency", {"latency": DB_LATENCY_MS}),
    ]
    for inject in scenarios:
        inject()
        checkout()
        # Remove the fault without clearing data: the orders it left behind are what P9 checks.
        clear_faults()


def test_p9_no_orders_stuck_pending_after_faults():
    """P9: After checkouts under every kind of fault, no order is left PENDING once faults clear."""
    run_fault_scenarios()
    left = wait_until(lambda: not pending_orders(), MAX_PENDING_SECONDS)
    assert left, f"orders still PENDING after {MAX_PENDING_SECONDS}s: {pending_orders()}"


def test_p10_slow_db_gives_graceful_error_within_3s():
    """P10: When the orders DB takes 1.5 s per round trip, checkout answers within 3 s with a JSON
    error, and the service keeps working once the DB is fast again."""
    add_toxic("order_db", "latency", {"latency": DB_LATENCY_MS})
    resp, elapsed = checkout()
    assert elapsed <= MAX_CHECKOUT_SECONDS, f"answered in {elapsed:.2f}s"
    assert resp.status_code in (503, 504), f"got {resp.status_code}: {resp.text}"
    assert resp.json().get("error"), resp.text

    clear_faults()
    assert http.get(f"{ORDER}/health").status_code == 200, "Order unhealthy after DB latency removed"
    ok, _ = checkout()
    assert ok.status_code == 200, f"checkout failed after DB latency removed: {ok.text}"
