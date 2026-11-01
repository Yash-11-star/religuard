"""Payment service.

Records every charge, deduplicates by Idempotency-Key, and exposes admin endpoints that the
reliability property checks use to count charges/attempts (P4, P5, P6, P8) and to force
HTTP 503s or declines, which Toxiproxy cannot produce at the TCP level.
"""
import os
from contextlib import asynccontextmanager
from decimal import Decimal
from typing import Literal

import asyncpg
from fastapi import FastAPI, Header
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://religuard:religuard@postgres:5432/payments")

SCHEMA = """
CREATE TABLE IF NOT EXISTS charges (
    id              BIGSERIAL PRIMARY KEY,
    order_id        TEXT NOT NULL,
    amount          NUMERIC(12, 2) NOT NULL,
    idempotency_key TEXT NOT NULL UNIQUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
-- One row per incoming POST /charge, whatever the outcome. Used to count attempts (P4).
CREATE TABLE IF NOT EXISTS charge_requests (
    id              BIGSERIAL PRIMARY KEY,
    order_id        TEXT NOT NULL,
    idempotency_key TEXT,
    outcome         TEXT NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
"""

# Injected fault for the next `remaining` /charge calls. One uvicorn worker, so module state is fine.
fault = {"mode": "none", "remaining": 0}


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.pool = await asyncpg.create_pool(DATABASE_URL, min_size=1, max_size=10, command_timeout=5)
    async with app.state.pool.acquire() as con:
        await con.execute(SCHEMA)
    yield
    await app.state.pool.close()


app = FastAPI(title="payment", lifespan=lifespan)


class ChargeRequest(BaseModel):
    order_id: str = Field(min_length=1)
    amount: Decimal = Field(gt=0, max_digits=12, decimal_places=2)


class FaultRequest(BaseModel):
    mode: Literal["none", "503", "decline"]
    count: int = Field(default=1, ge=0)


def take_fault() -> str:
    if fault["remaining"] <= 0:
        return "none"
    fault["remaining"] -= 1
    mode = fault["mode"]
    if fault["remaining"] == 0:
        fault["mode"] = "none"
    return mode


async def record(con, order_id: str, key: str | None, outcome: str) -> None:
    await con.execute(
        "INSERT INTO charge_requests (order_id, idempotency_key, outcome) VALUES ($1, $2, $3)",
        order_id, key, outcome,
    )


def error(status: int, code: str) -> JSONResponse:
    return JSONResponse({"error": code}, status_code=status)


def charge_body(row, replayed: bool) -> dict:
    return {
        "charge_id": row["id"],
        "order_id": row["order_id"],
        "amount": str(row["amount"]),
        "status": "charged",
        "replayed": replayed,
    }


@app.post("/charge")
async def charge(req: ChargeRequest, idempotency_key: str | None = Header(default=None)):
    async with app.state.pool.acquire() as con:
        if not idempotency_key:
            await record(con, req.order_id, None, "missing_key")
            return error(400, "missing_idempotency_key")

        mode = take_fault()
        if mode == "503":
            await record(con, req.order_id, idempotency_key, "fault_503")
            return error(503, "payment_unavailable")
        if mode == "decline":
            await record(con, req.order_id, idempotency_key, "declined")
            return error(402, "card_declined")

        # ON CONFLICT makes concurrent duplicates safe: exactly one insert wins.
        row = await con.fetchrow(
            """INSERT INTO charges (order_id, amount, idempotency_key) VALUES ($1, $2, $3)
               ON CONFLICT (idempotency_key) DO NOTHING
               RETURNING id, order_id, amount""",
            req.order_id, req.amount, idempotency_key,
        )
        if row is not None:
            await record(con, req.order_id, idempotency_key, "charged")
            return charge_body(row, replayed=False)

        row = await con.fetchrow(
            "SELECT id, order_id, amount FROM charges WHERE idempotency_key = $1", idempotency_key
        )
        if row["order_id"] != req.order_id or row["amount"] != req.amount:
            await record(con, req.order_id, idempotency_key, "key_conflict")
            return error(409, "idempotency_key_reused_with_different_request")
        await record(con, req.order_id, idempotency_key, "replayed")
        return charge_body(row, replayed=True)


@app.get("/health")
async def health():
    async with app.state.pool.acquire() as con:
        await con.fetchval("SELECT 1")
    return {"status": "ok"}


@app.get("/admin/charges")
async def admin_charges(order_id: str | None = None):
    async with app.state.pool.acquire() as con:
        rows = await con.fetch(
            """SELECT id, order_id, amount, idempotency_key, created_at FROM charges
               WHERE $1::text IS NULL OR order_id = $1 ORDER BY id""",
            order_id,
        )
    return [{**dict(r), "amount": str(r["amount"])} for r in rows]


@app.get("/admin/requests")
async def admin_requests(order_id: str | None = None):
    async with app.state.pool.acquire() as con:
        rows = await con.fetch(
            """SELECT id, order_id, idempotency_key, outcome, created_at FROM charge_requests
               WHERE $1::text IS NULL OR order_id = $1 ORDER BY id""",
            order_id,
        )
    return {"order_id": order_id, "attempts": len(rows), "requests": [dict(r) for r in rows]}


@app.get("/admin/fault")
async def get_fault():
    return fault


@app.post("/admin/fault")
async def set_fault(req: FaultRequest):
    fault["mode"] = req.mode if req.count > 0 else "none"
    fault["remaining"] = req.count if req.mode != "none" else 0
    return fault


@app.post("/admin/reset")
async def reset():
    fault.update(mode="none", remaining=0)
    async with app.state.pool.acquire() as con:
        await con.execute("TRUNCATE charges, charge_requests RESTART IDENTITY")
    return {"status": "reset"}
