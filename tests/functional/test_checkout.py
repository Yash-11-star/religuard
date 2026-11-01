"""Functional tests (#5): does the store work when nothing is broken? Run with `make up && make test-functional`.

These are the "do the tests pass" checks agents usually rely on. They never inject infrastructure
faults (no Toxiproxy toxics); a card decline is a normal business outcome, not a fault. The
reliability properties P1-P10 live in properties/.
"""
import os
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
        for base in (ORDER, PAYMENT, INVENTORY):
            c.post(f"{base}/admin/reset").raise_for_status()
        yield c


def checkout(client, key=None, sku="SKU-1", qty=2, amount="20.00"):
    return client.post(
        f"{ORDER}/checkout",
        json={"sku": sku, "qty": qty, "amount": amount},
        headers={"Idempotency-Key": key or uuid.uuid4().hex},
    )


def stock(client, sku="SKU-1"):
    s = client.get(f"{INVENTORY}/admin/stock/{sku}").json()
    return s["available"], s["reserved"]


def charges(client, order_id):
    return client.get(f"{PAYMENT}/admin/charges", params={"order_id": order_id}).json()


def test_happy_path_confirms_and_commits_stock(client):
    r = checkout(client, qty=2)
    assert r.status_code == 200
    order_id = r.json()["order_id"]
    assert r.json()["status"] == "CONFIRMED"
    assert client.get(f"{ORDER}/orders/{order_id}").json()["status"] == "CONFIRMED"
    assert stock(client) == (98, 0)
    assert len(charges(client, order_id)) == 1


def test_repeated_key_returns_same_order_and_charges_once(client):
    key = uuid.uuid4().hex
    first = checkout(client, key).json()
    second = checkout(client, key)
    assert second.status_code == 200
    assert second.json()["order_id"] == first["order_id"]
    assert len(charges(client, first["order_id"])) == 1
    assert stock(client) == (98, 0)


def test_key_reused_for_different_request_is_rejected(client):
    key = uuid.uuid4().hex
    checkout(client, key, qty=2)
    r = checkout(client, key, qty=7)
    assert r.status_code == 409
    assert r.json()["error"] == "idempotency_key_reused_with_different_request"


def test_out_of_stock(client):
    r = checkout(client, sku="SKU-3", qty=1)
    assert r.status_code == 409
    assert r.json()["error"] == "out_of_stock"
    assert client.get(f"{ORDER}/orders/{r.json()['order_id']}").json()["status"] == "FAILED"


def test_unknown_sku(client):
    r = checkout(client, sku="NOPE")
    assert r.status_code == 404
    assert r.json()["error"] == "unknown_sku"


def test_declined_payment_fails_order_and_releases_stock(client):
    client.post(f"{PAYMENT}/admin/fault", json={"mode": "decline", "count": 1}).raise_for_status()
    r = checkout(client, qty=3)
    assert r.status_code == 402
    assert r.json()["error"] == "card_declined"
    assert client.get(f"{ORDER}/orders/{r.json()['order_id']}").json()["status"] == "FAILED"
    assert stock(client) == (100, 0)


def test_invalid_input(client):
    r = client.post(f"{ORDER}/checkout", json={"sku": "SKU-1", "qty": 0, "amount": "1.00"})
    assert r.status_code == 422


def test_unknown_order(client):
    assert client.get(f"{ORDER}/orders/does-not-exist").status_code == 404


def test_admin_orders_filters_by_status(client):
    checkout(client)
    checkout(client, sku="SKU-3", qty=1)
    statuses = {s: len(client.get(f"{ORDER}/admin/orders", params={"status": s}).json())
                for s in ("CONFIRMED", "FAILED", "PENDING")}
    assert statuses == {"CONFIRMED": 1, "FAILED": 1, "PENDING": 0}
