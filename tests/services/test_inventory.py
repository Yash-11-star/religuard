"""API tests for the Inventory service (#3). Run against the live stack: `make up && make test-services`."""
import os
import uuid
from concurrent.futures import ThreadPoolExecutor

import httpx
import pytest

INVENTORY = os.environ.get("INVENTORY_URL", "http://localhost:8002")


@pytest.fixture
def client():
    with httpx.Client(base_url=INVENTORY, timeout=5) as c:
        c.post("/admin/reset").raise_for_status()
        yield c


def new_order():
    return f"order-{uuid.uuid4().hex[:8]}"


def reserve(client, order_id, sku="SKU-1", qty=2):
    return client.post("/reserve", json={"order_id": order_id, "sku": sku, "qty": qty})


def stock(client, sku="SKU-1"):
    s = client.get(f"/admin/stock/{sku}").json()
    return s["available"], s["reserved"]


def test_reset_seeds_stock(client):
    assert client.get("/admin/stock").json() == [
        {"sku": "SKU-1", "available": 100, "reserved": 0},
        {"sku": "SKU-2", "available": 100, "reserved": 0},
        {"sku": "SKU-3", "available": 0, "reserved": 0},
    ]


def test_reserve_moves_available_to_reserved(client):
    r = reserve(client, new_order(), qty=3)
    assert r.status_code == 200
    assert r.json()["status"] == "RESERVED"
    assert stock(client) == (97, 3)


def test_reserve_twice_reserves_once(client):
    order = new_order()
    reserve(client, order)
    second = reserve(client, order)
    assert second.status_code == 200
    assert second.json()["replayed"] is True
    assert stock(client) == (98, 2)


def test_concurrent_reserves_for_same_order_reserve_once(client):
    order = new_order()
    with ThreadPoolExecutor(max_workers=8) as pool:
        codes = list(pool.map(lambda _: reserve(client, order).status_code, range(8)))
    assert codes == [200] * 8
    assert stock(client) == (98, 2)
    assert len(client.get("/admin/reservations", params={"order_id": order}).json()) == 1


def test_same_order_different_reservation_is_rejected(client):
    order = new_order()
    reserve(client, order, qty=2)
    assert reserve(client, order, qty=5).status_code == 409
    assert stock(client) == (98, 2)


def test_out_of_stock_leaves_no_reservation(client):
    order = new_order()
    r = reserve(client, order, sku="SKU-3", qty=1)
    assert r.status_code == 409
    assert r.json()["error"] == "out_of_stock"
    assert client.get("/admin/reservations", params={"order_id": order}).json() == []
    # The order can still reserve something else afterwards.
    assert reserve(client, order, sku="SKU-1", qty=1).status_code == 200


def test_unknown_sku(client):
    assert reserve(client, new_order(), sku="NOPE").status_code == 404


def test_release_returns_stock_and_is_idempotent(client):
    order = new_order()
    reserve(client, order, qty=4)
    first = client.post("/release", json={"order_id": order})
    second = client.post("/release", json={"order_id": order})
    assert first.json()["status"] == "RELEASED"
    assert second.status_code == 200 and second.json()["replayed"] is True
    assert stock(client) == (100, 0)


def test_commit_consumes_stock_and_is_idempotent(client):
    order = new_order()
    reserve(client, order, qty=4)
    client.post("/commit", json={"order_id": order}).raise_for_status()
    second = client.post("/commit", json={"order_id": order})
    assert second.json()["replayed"] is True
    assert stock(client) == (96, 0)


def test_cannot_release_after_commit_or_commit_after_release(client):
    committed, released = new_order(), new_order()
    reserve(client, committed)
    reserve(client, released)
    client.post("/commit", json={"order_id": committed})
    client.post("/release", json={"order_id": released})
    assert client.post("/release", json={"order_id": committed}).status_code == 409
    assert client.post("/commit", json={"order_id": released}).status_code == 409


def test_release_unknown_order(client):
    r = client.post("/release", json={"order_id": new_order()})
    assert r.status_code == 404
    assert r.json()["error"] == "reservation_not_found"
