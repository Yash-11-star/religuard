"""Order service.

Checkout: create a PENDING order -> reserve stock (Inventory) -> charge (Payment) -> commit stock -> CONFIRMED.

Version 0 is written to satisfy every reliability property (P1-P10):
  - every call to Payment, Inventory, and the orders DB goes through Toxiproxy and has a timeout
  - at most MAX_ATTEMPTS tries per dependency call, exponential backoff with jitter, retrying only
    timeouts, connection errors, and 502/503/504
  - the client always gets an answer within CHECKOUT_DEADLINE seconds
  - every retry of a charge sends the same Payment Idempotency-Key, so it is never applied twice
  - a failed checkout releases its reservation
  - no order stays PENDING: finishing an order (commit/release + final status) runs as a background
    task that retries until it succeeds, and a reaper fails PENDING orders that nobody is finishing
"""
import asyncio
import os
import random
import time
import uuid
from contextlib import asynccontextmanager
from decimal import Decimal

import asyncpg
import httpx
from fastapi import FastAPI, Header
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://religuard:religuard@toxiproxy:15432/orders")
PAYMENT_URL = os.environ.get("PAYMENT_URL", "http://toxiproxy:18001")
INVENTORY_URL = os.environ.get("INVENTORY_URL", "http://toxiproxy:18002")

ATTEMPT_TIMEOUT = 1.0       # seconds per call to Payment or Inventory
MAX_ATTEMPTS = 3            # tries per call, including the first
BACKOFF_BASE = 0.1          # seconds; before retry n we wait BACKOFF_BASE * 2**n, +-50% jitter
CHECKOUT_DEADLINE = 2.5     # seconds; every checkout answers within this
DB_TIMEOUT = 1.0            # seconds per DB statement (including getting a connection)
STALE_PENDING_AFTER = 3.0   # seconds; the reaper fails older PENDING orders that nobody is finishing
RETRYABLE_STATUS = {502, 503, 504}

# Error code -> HTTP status returned to the client.
ERROR_STATUS = {
    "out_of_stock": 409,
    "unknown_sku": 404,
    "card_declined": 402,
    "idempotency_key_reused_with_different_request": 409,
    "payment_unavailable": 503,
    "payment_timeout": 504,
    "inventory_unavailable": 503,
    "inventory_timeout": 504,
    "database_unavailable": 503,
    "deadline_exceeded": 504,
    "internal_error": 500,
}

SCHEMA = """
CREATE TABLE IF NOT EXISTS orders (
    id              TEXT PRIMARY KEY,
    idempotency_key TEXT NOT NULL UNIQUE,
    sku             TEXT NOT NULL,
    qty             INTEGER NOT NULL,
    amount          NUMERIC(12, 2) NOT NULL,
    status          TEXT NOT NULL,          -- PENDING | CONFIRMED | FAILED
    error           TEXT,
    charge_id       BIGINT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
"""

# order_id -> background task finishing that order. One uvicorn worker, so module state is fine.
finalizers: dict[str, asyncio.Task] = {}
# DB statements we stopped waiting for (see db()); /admin/reset waits for them so nothing lands late.
db_stragglers: set[asyncio.Task] = set()


class CheckoutFailed(Exception):
    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


class Deadline:
    def __init__(self, seconds: float):
        self.at = time.monotonic() + seconds

    def remaining(self) -> float:
        return self.at - time.monotonic()


class CheckoutRequest(BaseModel):
    sku: str = Field(min_length=1)
    qty: int = Field(gt=0)
    amount: Decimal = Field(gt=0, max_digits=12, decimal_places=2)


# ---------------------------------------------------------------- dependencies


async def db(method: str, query: str, *args, timeout: float = DB_TIMEOUT):
    """Run one statement on the orders DB; give up waiting after `timeout` (connection wait included).

    On timeout the statement is left to finish in the background instead of being cancelled:
    cancelling an asyncpg query waits for a cancel round trip to the (slow) server, which would
    blow the checkout deadline. A late INSERT that lands this way is failed by the reaper.
    """
    if timeout <= 0:
        raise CheckoutFailed("database_unavailable")

    async def run():
        async with app.state.pool.acquire() as con:
            return await getattr(con, method)(query, *args)

    task = asyncio.create_task(run())
    done, _ = await asyncio.wait({task}, timeout=timeout)
    if not done:
        db_stragglers.add(task)
        task.add_done_callback(lambda t: (db_stragglers.discard(t), t.cancelled() or t.exception()))
        raise CheckoutFailed("database_unavailable")
    try:
        return task.result()
    except (OSError, asyncpg.PostgresError, asyncpg.InterfaceError) as exc:
        raise CheckoutFailed("database_unavailable") from exc


async def call(dependency: str, url: str, deadline: Deadline, **kwargs) -> httpx.Response:
    """POST to Payment or Inventory with a per-attempt timeout, bounded retries, and backoff.

    Returns the first non-retryable response. Raises CheckoutFailed("<dependency>_timeout" or
    "<dependency>_unavailable") when attempts or the deadline run out.
    """
    timed_out = False
    for attempt in range(MAX_ATTEMPTS):
        budget = min(ATTEMPT_TIMEOUT, deadline.remaining())
        if budget <= 0:
            break
        try:
            async with asyncio.timeout(budget):
                resp = await app.state.http.post(url, **kwargs)
            if resp.status_code not in RETRYABLE_STATUS:
                return resp
            timed_out = False
        except (TimeoutError, httpx.TimeoutException):
            timed_out = True
        except httpx.TransportError:
            timed_out = False
        if attempt + 1 < MAX_ATTEMPTS:
            delay = BACKOFF_BASE * 2**attempt * random.uniform(0.5, 1.5)
            if delay >= deadline.remaining():
                break
            await asyncio.sleep(delay)
    raise CheckoutFailed(f"{dependency}_{'timeout' if timed_out else 'unavailable'}")


def error_code(resp: httpx.Response) -> str | None:
    try:
        return resp.json().get("error")
    except ValueError:
        return None


async def reserve(order_id: str, req: CheckoutRequest, deadline: Deadline) -> None:
    resp = await call(
        "inventory", f"{INVENTORY_URL}/reserve", deadline,
        json={"order_id": order_id, "sku": req.sku, "qty": req.qty},
    )
    if resp.status_code == 200:
        return
    code = error_code(resp)
    raise CheckoutFailed(code if code in ("out_of_stock", "unknown_sku") else "inventory_unavailable")


async def charge(order_id: str, amount: Decimal, deadline: Deadline) -> dict:
    resp = await call(
        "payment", f"{PAYMENT_URL}/charge", deadline,
        json={"order_id": order_id, "amount": str(amount)},
        headers={"Idempotency-Key": f"order-{order_id}"},  # same key on every retry
    )
    if resp.status_code == 200:
        return resp.json()
    raise CheckoutFailed("card_declined" if resp.status_code == 402 else "payment_unavailable")


# ---------------------------------------------------------------- finishing orders


async def inventory_transition(action: str, order_id: str) -> None:
    """Commit or release a reservation. 404 (never reserved) and 409 (already settled) are final."""
    resp = await call("inventory", f"{INVENTORY_URL}/{action}", Deadline(5), json={"order_id": order_id})
    if resp.status_code not in (200, 404, 409):
        raise CheckoutFailed("inventory_unavailable")


async def finalize(order_id: str, status: str, error: str | None, release: bool, charge_id: int | None) -> None:
    """Settle the reservation, then write the final status. Retries until it succeeds."""
    delay = BACKOFF_BASE
    while True:
        try:
            if status == "CONFIRMED":
                await inventory_transition("commit", order_id)
            elif release:
                await inventory_transition("release", order_id)
            await db(
                "execute",
                """UPDATE orders SET status = $2, error = $3, charge_id = $4, updated_at = now()
                   WHERE id = $1 AND status = 'PENDING'""",
                order_id, status, error, charge_id,
            )
            return
        except CheckoutFailed:
            await asyncio.sleep(delay)
            delay = min(delay * 2, 2.0)


def start_finalizer(order_id: str, status: str, error: str | None, release: bool, charge_id: int | None = None):
    task = asyncio.create_task(finalize(order_id, status, error, release, charge_id))
    finalizers[order_id] = task
    task.add_done_callback(lambda _: finalizers.pop(order_id, None) if finalizers.get(order_id) is task else None)
    return task


async def reaper() -> None:
    """Fail PENDING orders that no request or finalizer is working on (e.g. an insert that landed late)."""
    while True:
        await asyncio.sleep(1)
        try:
            rows = await db(
                "fetch",
                "SELECT id FROM orders WHERE status = 'PENDING' AND updated_at < now() - make_interval(secs => $1)",
                STALE_PENDING_AFTER,
            )
        except CheckoutFailed:
            continue
        for row in rows:
            if row["id"] not in finalizers:
                start_finalizer(row["id"], "FAILED", "deadline_exceeded", release=True)


# ---------------------------------------------------------------- responses


def order_body(row) -> dict:
    return {
        "order_id": row["id"],
        "status": row["status"],
        "sku": row["sku"],
        "qty": row["qty"],
        "amount": str(row["amount"]),
        "charge_id": row["charge_id"],
        "error": row["error"],
        "created_at": row["created_at"].isoformat(),
        "updated_at": row["updated_at"].isoformat(),
    }


def failure(order_id: str | None, code: str) -> JSONResponse:
    return JSONResponse(
        {"error": code, "order_id": order_id, "status": "FAILED"}, status_code=ERROR_STATUS.get(code, 500)
    )


def order_response(row) -> JSONResponse:
    if row["status"] == "FAILED":
        return failure(row["id"], row["error"] or "internal_error")
    return JSONResponse(order_body(row), status_code=200 if row["status"] == "CONFIRMED" else 202)


async def finish(order_id: str, status: str, error: str | None, deadline: Deadline,
                 release: bool = False, charge_id: int | None = None) -> JSONResponse:
    """Finish the order in the background and wait for it only until the checkout deadline."""
    task = start_finalizer(order_id, status, error, release, charge_id)
    try:
        await asyncio.wait_for(asyncio.shield(task), timeout=max(deadline.remaining(), 0))
    except TimeoutError:
        pass  # keeps running in the background
    if status == "FAILED":
        return failure(order_id, error)
    if task.done():
        return JSONResponse({"order_id": order_id, "status": "CONFIRMED", "charge_id": charge_id}, status_code=200)
    # Paid, but stock commit / status write is still in progress.
    return JSONResponse({"order_id": order_id, "status": "PENDING", "charge_id": charge_id}, status_code=202)


async def existing_order(key: str, req: CheckoutRequest, deadline: Deadline) -> JSONResponse:
    """Repeated Idempotency-Key: return that order, waiting (within the deadline) if it is still running."""
    while True:
        try:
            row = await db(
                "fetchrow", "SELECT * FROM orders WHERE idempotency_key = $1", key,
                timeout=min(DB_TIMEOUT, deadline.remaining()),
            )
        except CheckoutFailed as exc:
            return failure(None, exc.code)
        if (row["sku"], row["qty"], row["amount"]) != (req.sku, req.qty, req.amount):
            return failure(row["id"], "idempotency_key_reused_with_different_request")
        if row["status"] != "PENDING" or deadline.remaining() < 0.2:
            return order_response(row)
        await asyncio.sleep(0.1)


# ---------------------------------------------------------------- app


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.pool = await asyncpg.create_pool(DATABASE_URL, min_size=2, max_size=20)
    async with app.state.pool.acquire() as con:
        await con.execute(SCHEMA)
    app.state.http = httpx.AsyncClient(timeout=ATTEMPT_TIMEOUT)
    reaper_task = asyncio.create_task(reaper())
    yield
    reaper_task.cancel()
    for task in list(finalizers.values()):
        task.cancel()
    await app.state.http.aclose()
    await app.state.pool.close()


app = FastAPI(title="order", lifespan=lifespan)


@app.exception_handler(Exception)
async def unhandled(request, exc):
    return failure(None, "internal_error")


@app.post("/checkout")
async def checkout(req: CheckoutRequest, idempotency_key: str | None = Header(default=None)):
    deadline = Deadline(CHECKOUT_DEADLINE)
    key = idempotency_key or uuid.uuid4().hex
    order_id = uuid.uuid4().hex

    try:
        created = await db(
            "fetchval",
            """INSERT INTO orders (id, idempotency_key, sku, qty, amount, status)
               VALUES ($1, $2, $3, $4, $5, 'PENDING')
               ON CONFLICT (idempotency_key) DO NOTHING RETURNING id""",
            order_id, key, req.sku, req.qty, req.amount,
            timeout=min(DB_TIMEOUT, deadline.remaining()),
        )
    except CheckoutFailed as exc:
        # The insert may still land after we gave up; the reaper fails it if so.
        return failure(order_id, exc.code)
    if created is None:
        return await existing_order(key, req, deadline)

    try:
        await reserve(order_id, req, deadline)
    except CheckoutFailed as exc:
        # A timed-out reserve may still have reserved stock, so release unless Inventory said no.
        rejected = exc.code in ("out_of_stock", "unknown_sku")
        return await finish(order_id, "FAILED", exc.code, deadline, release=not rejected)
    except Exception:
        return await finish(order_id, "FAILED", "internal_error", deadline, release=True)

    try:
        paid = await charge(order_id, req.amount, deadline)
    except CheckoutFailed as exc:
        return await finish(order_id, "FAILED", exc.code, deadline, release=True)
    except Exception:
        return await finish(order_id, "FAILED", "internal_error", deadline, release=True)

    return await finish(order_id, "CONFIRMED", None, deadline, charge_id=paid["charge_id"])


@app.get("/orders/{order_id}")
async def get_order(order_id: str):
    try:
        row = await db("fetchrow", "SELECT * FROM orders WHERE id = $1", order_id)
    except CheckoutFailed as exc:
        return failure(order_id, exc.code)
    if row is None:
        return JSONResponse({"error": "order_not_found"}, status_code=404)
    return order_body(row)


@app.get("/health")
async def health():
    try:
        await db("fetchval", "SELECT 1")
    except CheckoutFailed:
        return JSONResponse({"status": "database_unavailable"}, status_code=503)
    return {"status": "ok"}


@app.get("/admin/orders")
async def admin_orders(status: str | None = None):
    rows = await db(
        "fetch", "SELECT * FROM orders WHERE $1::text IS NULL OR status = $1 ORDER BY created_at", status,
        timeout=5,
    )
    return [order_body(r) for r in rows]


@app.post("/admin/reset")
async def reset():
    for task in list(finalizers.values()):
        task.cancel()
    finalizers.clear()
    if db_stragglers:
        await asyncio.wait(set(db_stragglers), timeout=10)
    await db("execute", "TRUNCATE orders", timeout=5)
    return {"status": "reset"}
