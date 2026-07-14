import os
from contextlib import contextmanager

import psycopg
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field


DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://ticket:ticket@localhost:5432/ticketdb")
DEFAULT_EVENT_ID = os.getenv("DEFAULT_EVENT_ID", "concert-1")
DEFAULT_SEATS = int(os.getenv("DEFAULT_SEATS", "10"))

app = FastAPI(title="Inventory Service", version="0.1.0")


class InventoryRequest(BaseModel):
    event_id: str = Field(default="concert-1")
    seat_id: str = Field(default="A1")
    user_id: str = Field(default="user-1")


@contextmanager
def db_connection():
    conn = psycopg.connect(DATABASE_URL)
    try:
        yield conn
    finally:
        conn.close()


def initialize_database() -> None:
    with db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS seats (
                    event_id TEXT NOT NULL,
                    seat_id TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'available',
                    reserved_by TEXT,
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                    PRIMARY KEY (event_id, seat_id)
                );
                """
            )
            for i in range(1, DEFAULT_SEATS + 1):
                cur.execute(
                    """
                    INSERT INTO seats (event_id, seat_id, status)
                    VALUES (%s, %s, 'available')
                    ON CONFLICT (event_id, seat_id) DO NOTHING;
                    """,
                    (DEFAULT_EVENT_ID, f"A{i}"),
                )
        conn.commit()


@app.on_event("startup")
def startup() -> None:
    initialize_database()


@app.get("/health")
async def health() -> dict[str, str]:
    try:
        with db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1;")
                cur.fetchone()
        return {"status": "ok", "service": "inventory"}
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"database unavailable: {exc}") from exc


@app.get("/inventory/{event_id}")
async def list_inventory(event_id: str) -> dict:
    with db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT seat_id, status, reserved_by
                FROM seats
                WHERE event_id = %s
                ORDER BY seat_id;
                """,
                (event_id,),
            )
            rows = cur.fetchall()

    return {
        "event_id": event_id,
        "seats": [
            {"seat_id": seat_id, "status": status, "reserved_by": reserved_by}
            for seat_id, status, reserved_by in rows
        ],
    }


@app.post("/inventory/reserve")
async def reserve_seat(request: InventoryRequest) -> dict:
    with db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("BEGIN;")
            cur.execute(
                """
                SELECT status
                FROM seats
                WHERE event_id = %s AND seat_id = %s
                FOR UPDATE;
                """,
                (request.event_id, request.seat_id),
            )
            row = cur.fetchone()

            if row is None:
                conn.rollback()
                raise HTTPException(status_code=404, detail="seat not found")

            if row[0] != "available":
                conn.rollback()
                raise HTTPException(status_code=409, detail="seat is not available")

            cur.execute(
                """
                UPDATE seats
                SET status = 'reserved', reserved_by = %s, updated_at = now()
                WHERE event_id = %s AND seat_id = %s;
                """,
                (request.user_id, request.event_id, request.seat_id),
            )
        conn.commit()

    return {
        "event_id": request.event_id,
        "seat_id": request.seat_id,
        "status": "reserved",
        "reserved_by": request.user_id,
    }


@app.post("/inventory/release")
async def release_seat(request: InventoryRequest) -> dict:
    with db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE seats
                SET status = 'available', reserved_by = NULL, updated_at = now()
                WHERE event_id = %s AND seat_id = %s AND reserved_by = %s;
                """,
                (request.event_id, request.seat_id, request.user_id),
            )
        conn.commit()

    return {
        "event_id": request.event_id,
        "seat_id": request.seat_id,
        "status": "released",
    }
