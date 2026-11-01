"""API tests for the Order service (#4). Run against the live stack: `make up && make test-services`.

The no-fault checkout tests moved to tests/functional/ (#5). This keeps #4's "done when" check;
the full fault-injection properties P1-P10 live in properties/.
"""
import os
import time
import uuid

import httpx
import pytest

ORDER = os.environ.get("ORDER_URL", "http://localhost:8000")
PAYMENT = os.environ.get("PAYMENT_URL", "http://localhost:8001")
INVENTORY = os.environ.get("INVENTORY_URL", "http://localhost:8002")
TOXIPROXY = os.environ.get("TOXIPROXY_URL", "http://localhost:8474")


@pytest.fixture
def client():
    with httpx.Client(timeout=10) as c:
        c.post(f"{TOXIPROXY}/reset").raise_for_status()
        for base in (ORDER, PAYMENT, INVENTORY):  # Order first, so its finalizers stop first
            c.post(f"{base}/admin/reset").raise_for_status()
        yield c
        c.post(f"{TOXIPROXY}/reset")


def test_slow_payment_still_answers_within_3s(client):
    """#4 'done when': 5 s of latency on Payment gives an error in under 3 s."""
    client.post(
        f"{TOXIPROXY}/proxies/payment/toxics",
        json={"type": "latency", "attributes": {"latency": 5000}},
    ).raise_for_status()
    t0 = time.monotonic()
    r = client.post(
        f"{ORDER}/checkout",
        json={"sku": "SKU-1", "qty": 2, "amount": "20.00"},
        headers={"Idempotency-Key": uuid.uuid4().hex},
    )
    elapsed = time.monotonic() - t0
    assert r.status_code == 504
    assert r.json()["error"] == "payment_timeout"
    assert elapsed < 3
