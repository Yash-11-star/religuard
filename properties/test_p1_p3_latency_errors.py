"""P1-P3 (#7): bounded latency and graceful errors when a dependency is slow or down."""
from helpers import add_toxic, checkout, disable_proxy

DEPENDENCY_LATENCY_MS = 5000    # P1, P2: injected latency on every response from the dependency
MAX_CHECKOUT_SECONDS = 3.0      # P1-P3: checkout must answer within this


def assert_json_error(resp):
    assert resp.headers.get("content-type", "").startswith("application/json"), resp.text
    error = resp.json().get("error")
    assert isinstance(error, str) and error, f"no error code in body: {resp.text}"


def test_p1_slow_payment_gives_error_within_3s():
    """P1: When Payment takes 5 s to respond, checkout still answers with an error within 3 s."""
    add_toxic("payment", "latency", {"latency": DEPENDENCY_LATENCY_MS})
    resp, elapsed = checkout()
    assert elapsed <= MAX_CHECKOUT_SECONDS, f"answered in {elapsed:.2f}s"
    assert resp.status_code >= 500, f"expected an error, got {resp.status_code}: {resp.text}"
    assert_json_error(resp)


def test_p2_slow_inventory_gives_error_within_3s():
    """P2: When Inventory takes 5 s to respond, checkout still answers with an error within 3 s."""
    add_toxic("inventory", "latency", {"latency": DEPENDENCY_LATENCY_MS})
    resp, elapsed = checkout()
    assert elapsed <= MAX_CHECKOUT_SECONDS, f"answered in {elapsed:.2f}s"
    assert resp.status_code >= 500, f"expected an error, got {resp.status_code}: {resp.text}"
    assert_json_error(resp)


def test_p3_payment_down_gives_clean_503():
    """P3: When Payment is down, checkout answers with a 503 and a JSON error body, without hanging."""
    disable_proxy("payment")
    resp, elapsed = checkout()
    assert elapsed <= MAX_CHECKOUT_SECONDS, f"answered in {elapsed:.2f}s"
    assert resp.status_code == 503, f"got {resp.status_code}: {resp.text}"
    assert_json_error(resp)
