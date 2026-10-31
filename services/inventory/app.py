"""Inventory service.

Order reserves stock before charging, then commits it on success or releases it on failure.
Every operation is idempotent per order_id, so retries from Order are safe. The admin endpoints
let the property checks see stock levels before and after a fault (P8).
"""
import os
from contextlib import asynccontextmanager

import asyncpg
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://religuard:religuard@postgres:5432/inventory")

# sku -> starting available quantity. SKU-3 is always out of stock (for functional tests).
SEED_STOCK = {"SKU-1": 100, "SKU-2": 100, "SKU-3": 0}

SCHEMA = """
CREATE TABLE IF NOT EXISTS stock (
    sku       TEXT PRIMARY KEY,
    available INTEGER NOT NULL CHECK (available >= 0),
    reserved  INTEGER NOT NULL DEFAULT 0 CHECK (reserved >= 0)
);
-- One reservation per order. status: RESERVED -> COMMITTED, or RESERVED -> RELEASED.
CREATE TABLE IF NOT EXISTS reservations (
    id         BIGSERIAL PRIMARY KEY,
    order_id   TEXT NOT NULL UNIQUE,
    sku        TEXT NOT NULL REFERENCES stock (sku),
    qty        INTEGER NOT NULL CHECK (qty > 0),
    status     TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
"""


async def seed(con) -> None:
    await con.execute("TRUNCATE reservations, stock RESTART IDENTITY")
    await con.executemany("INSERT INTO stock (sku, available) VALUES ($1, $2)", SEED_STOCK.items())


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.pool = await asyncpg.create_pool(DATABASE_URL, min_size=1, max_size=10, command_timeout=5)
    async with app.state.pool.acquire() as con:
        await con.execute(SCHEMA)
        if await con.fetchval("SELECT count(*) FROM stock") == 0:
            await seed(con)
    yield
    await app.state.pool.close()


app = FastAPI(title="inventory", lifespan=lifespan)


class ReserveRequest(BaseModel):
    order_id: str = Field(min_length=1)
    sku: str = Field(min_length=1)
    qty: int = Field(gt=0)


class OrderRef(BaseModel):
    order_id: str = Field(min_length=1)


def error(status: int, code: str) -> JSONResponse:
    return JSONResponse({"error": code}, status_code=status)


def reservation_body(row, replayed: bool = False) -> dict:
    return {
        "order_id": row["order_id"],
        "sku": row["sku"],
        "qty": row["qty"],
        "status": row["status"],
        "replayed": replayed,
    }


class OutOfStock(Exception):
    """Raised inside the reserve transaction so the new reservation row is rolled back."""


@app.exception_handler(OutOfStock)
async def out_of_stock_handler(request, exc):
    return error(409, "out_of_stock")


@app.post("/reserve")
async def reserve(req: ReserveRequest):
    async with app.state.pool.acquire() as con, con.transaction():
        if not await con.fetchval("SELECT 1 FROM stock WHERE sku = $1", req.sku):
            return error(404, "unknown_sku")

        # A concurrent reserve for the same order blocks here until the first one commits or rolls back.
        row = await con.fetchrow(
            """INSERT INTO reservations (order_id, sku, qty, status) VALUES ($1, $2, $3, 'RESERVED')
               ON CONFLICT (order_id) DO NOTHING
               RETURNING order_id, sku, qty, status""",
            req.order_id, req.sku, req.qty,
        )
        if row is None:
            existing = await con.fetchrow(
                "SELECT order_id, sku, qty, status FROM reservations WHERE order_id = $1", req.order_id
            )
            if existing["sku"] != req.sku or existing["qty"] != req.qty:
                return error(409, "order_already_has_different_reservation")
            return reservation_body(existing, replayed=True)

        taken = await con.fetchval(
            """UPDATE stock SET available = available - $2, reserved = reserved + $2
               WHERE sku = $1 AND available >= $2 RETURNING sku""",
            req.sku, req.qty,
        )
        if taken is None:
            raise OutOfStock()
        return reservation_body(row)


async def transition(order_id: str, target: str) -> JSONResponse | dict:
    """Move a reservation to RELEASED or COMMITTED. Repeating the same transition is a no-op."""
    async with app.state.pool.acquire() as con, con.transaction():
        row = await con.fetchrow(
            "SELECT order_id, sku, qty, status FROM reservations WHERE order_id = $1 FOR UPDATE", order_id
        )
        if row is None:
            return error(404, "reservation_not_found")
        if row["status"] == target:
            return reservation_body(row, replayed=True)
        if row["status"] != "RESERVED":
            return error(409, f"reservation_already_{row['status'].lower()}")

        if target == "RELEASED":
            stock_change = "available = available + $2, reserved = reserved - $2"
        else:
            stock_change = "reserved = reserved - $2"
        await con.execute(f"UPDATE stock SET {stock_change} WHERE sku = $1", row["sku"], row["qty"])
        updated = await con.fetchrow(
            """UPDATE reservations SET status = $2, updated_at = now() WHERE order_id = $1
               RETURNING order_id, sku, qty, status""",
            order_id, target,
        )
        return reservation_body(updated)


@app.post("/release")
async def release(req: OrderRef):
    return await transition(req.order_id, "RELEASED")


@app.post("/commit")
async def commit(req: OrderRef):
    return await transition(req.order_id, "COMMITTED")


@app.get("/health")
async def health():
    async with app.state.pool.acquire() as con:
        await con.fetchval("SELECT 1")
    return {"status": "ok"}


@app.get("/admin/stock")
async def admin_all_stock():
    async with app.state.pool.acquire() as con:
        rows = await con.fetch("SELECT sku, available, reserved FROM stock ORDER BY sku")
    return [dict(r) for r in rows]


@app.get("/admin/stock/{sku}")
async def admin_stock(sku: str):
    async with app.state.pool.acquire() as con:
        row = await con.fetchrow("SELECT sku, available, reserved FROM stock WHERE sku = $1", sku)
    return dict(row) if row else error(404, "unknown_sku")


@app.get("/admin/reservations")
async def admin_reservations(order_id: str | None = None):
    async with app.state.pool.acquire() as con:
        rows = await con.fetch(
            """SELECT order_id, sku, qty, status, created_at, updated_at FROM reservations
               WHERE $1::text IS NULL OR order_id = $1 ORDER BY id""",
            order_id,
        )
    return [dict(r) for r in rows]


@app.post("/admin/reset")
async def reset():
    async with app.state.pool.acquire() as con, con.transaction():
        await seed(con)
    return {"status": "reset"}
