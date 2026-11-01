"""API tests for the Payment service (#2). Run against the live stack: `make up && make test-services`."""
import os
import uuid
from concurrent.futures import ThreadPoolExecutor

import httpx
import pytest

PAYMENT = os.environ.get("PAYMENT_URL", "http://localhost:8001")


@pytest.fixture
def client():
    with httpx.Client(base_url=PAYMENT, timeout=5) as c:
        c.post("/admin/reset").raise_for_status()
        yield c


def charge(client, order_id, key, amount="10.00"):
    return client.post("/charge", json={"order_id": order_id, "amount": amount}, headers={"Idempotency-Key": key})


def charges_for(client, order_id):
    return client.get("/admin/charges", params={"order_id": order_id}).json()


def attempts_for(client, order_id):
    return client.get("/admin/requests", params={"order_id": order_id}).json()["attempts"]


def new_ids():
    return f"order-{uuid.uuid4().hex[:8]}", uuid.uuid4().hex


def test_charge_creates_one_row(client):
    order, key = new_ids()
    r = charge(client, order, key)
    assert r.status_code == 200
    assert r.json()["replayed"] is False
    assert len(charges_for(client, order)) == 1


def test_same_key_twice_charges_once(client):
    order, key = new_ids()
    first = charge(client, order, key).json()
    second = charge(client, order, key).json()
    assert second["replayed"] is True
    assert second["charge_id"] == first["charge_id"]
    assert len(charges_for(client, order)) == 1


def test_concurrent_duplicates_charge_once(client):
    order, key = new_ids()
    with ThreadPoolExecutor(max_workers=8) as pool:
        codes = list(pool.map(lambda _: charge(client, order, key).status_code, range(8)))
    assert codes == [200] * 8
    assert len(charges_for(client, order)) == 1


def test_key_reused_for_different_request_is_rejected(client):
    order, key = new_ids()
    charge(client, order, key, amount="10.00")
    r = charge(client, order, key, amount="99.00")
    assert r.status_code == 409
    assert len(charges_for(client, order)) == 1


def test_missing_key_is_rejected(client):
    r = client.post("/charge", json={"order_id": "order-x", "amount": "10.00"})
    assert r.status_code == 400
    assert r.json()["error"] == "missing_idempotency_key"


def test_fault_503_then_recovers(client):
    order, key = new_ids()
    client.post("/admin/fault", json={"mode": "503", "count": 3}).raise_for_status()
    codes = [charge(client, order, key).status_code for _ in range(4)]
    assert codes == [503, 503, 503, 200]
    assert len(charges_for(client, order)) == 1
    assert client.get("/admin/fault").json() == {"mode": "none", "remaining": 0}


def test_decline_creates_no_charge(client):
    order, key = new_ids()
    client.post("/admin/fault", json={"mode": "decline", "count": 1}).raise_for_status()
    r = charge(client, order, key)
    assert r.status_code == 402
    assert r.json()["error"] == "card_declined"
    assert charges_for(client, order) == []


def test_attempt_counter_counts_every_request(client):
    order, key = new_ids()
    client.post("/admin/fault", json={"mode": "503", "count": 2}).raise_for_status()
    for _ in range(5):
        charge(client, order, key)
    assert attempts_for(client, order) == 5
    outcomes = [r["outcome"] for r in client.get("/admin/requests", params={"order_id": order}).json()["requests"]]
    assert outcomes == ["fault_503", "fault_503", "charged", "replayed", "replayed"]


def test_reset_clears_everything(client):
    order, key = new_ids()
    charge(client, order, key)
    client.post("/admin/fault", json={"mode": "503", "count": 5})
    client.post("/admin/reset").raise_for_status()
    assert client.get("/admin/charges").json() == []
    assert client.get("/admin/requests").json()["attempts"] == 0
    assert client.get("/admin/fault").json() == {"mode": "none", "remaining": 0}
