"""P4-P6 (#8): bounded retries and no duplicate charges."""
import uuid
from concurrent.futures import ThreadPoolExecutor

import pytest

from helpers import (
    add_toxic, attempts, charges, checkout, payment_requests, remove_toxic, set_payment_fault,
)

PAYMENT_503_BURST = 10          # P4: the next N /charge calls return 503
MAX_PAYMENT_ATTEMPTS = 3        # P4: Payment may see at most this many attempts per order
EXPECTED_CHARGES = 1            # P5, P6: exactly one charge per order


def test_p4_payment_503_burst_bounded_retries():
    """P4: When Payment keeps answering 503, Order tries it at most 3 times for that checkout."""
    set_payment_fault("503", PAYMENT_503_BURST)
    resp, _ = checkout()
    order_id = resp.json().get("order_id")
    assert order_id, f"no order_id in response: {resp.text}"
    assert resp.status_code >= 500, f"expected an error, got {resp.status_code}: {resp.text}"
    n = attempts(order_id)
    assert 1 <= n <= MAX_PAYMENT_ATTEMPTS, f"Payment received {n} attempts"


def test_p5_lost_charge_response_then_retry_charges_once():
    """P5: If Payment charges but its response never reaches Order, retrying the checkout with the
    same Idempotency-Key does not charge the customer a second time."""
    key = uuid.uuid4().hex
    # timeout toxic on the downstream stream: requests reach Payment (so it charges), but every
    # byte of its response is swallowed and the connection hangs until Order gives up.
    toxic = add_toxic("payment", "timeout", {"timeout": 0}, stream="downstream")
    first, _ = checkout(key=key)
    assert first.status_code >= 500, f"expected an error, got {first.status_code}: {first.text}"
    order_id = first.json()["order_id"]
    outcomes = [r["outcome"] for r in payment_requests(order_id)]
    assert "charged" in outcomes, f"fault did not reproduce a lost charge response: {outcomes}"

    remove_toxic("payment", toxic["name"])
    retry, _ = checkout(key=key)
    assert retry.json().get("order_id") == order_id, f"retry returned a different order: {retry.text}"
    assert len(charges(order_id)) == EXPECTED_CHARGES


@pytest.mark.parametrize("delivery", ["sequential", "concurrent"])
def test_p6_duplicate_delivery_charges_once(delivery):
    """P6: The same checkout delivered twice with the same Idempotency-Key charges once and returns
    the same order both times."""
    key = uuid.uuid4().hex
    if delivery == "sequential":
        responses = [checkout(key=key)[0], checkout(key=key)[0]]
    else:
        with ThreadPoolExecutor(2) as pool:
            responses = [f.result()[0] for f in [pool.submit(checkout, key=key) for _ in range(2)]]
    order_ids = {r.json().get("order_id") for r in responses}
    assert len(order_ids) == 1, f"different orders returned: {[r.text for r in responses]}"
    assert all(r.status_code == 200 for r in responses), [r.text for r in responses]
    assert len(charges(order_ids.pop())) == EXPECTED_CHARGES
