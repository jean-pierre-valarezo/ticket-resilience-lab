import asyncio
import os
import time
from enum import Enum
from uuid import uuid4

import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field


INVENTORY_URL = os.getenv("INVENTORY_URL", "http://localhost:8002")
PAYMENTS_URL = os.getenv("PAYMENTS_URL", "http://localhost:8003")
NOTIFICATIONS_URL = os.getenv("NOTIFICATIONS_URL", "http://localhost:8004")

INVENTORY_RETRY_ATTEMPTS = int(os.getenv("INVENTORY_RETRY_ATTEMPTS", "3"))
PAYMENT_TIMEOUT_SECONDS = float(os.getenv("PAYMENT_TIMEOUT_SECONDS", "3"))
PAYMENT_FAILURE_THRESHOLD = int(os.getenv("PAYMENT_FAILURE_THRESHOLD", "3"))
PAYMENT_CIRCUIT_RESET_SECONDS = float(os.getenv("PAYMENT_CIRCUIT_RESET_SECONDS", "15"))
NOTIFICATION_TIMEOUT_SECONDS = float(os.getenv("NOTIFICATION_TIMEOUT_SECONDS", "2"))

app = FastAPI(title="Reservations Service", version="0.1.0")


class ReservationRequest(BaseModel):
    event_id: str = Field(default="concert-1")
    seat_id: str = Field(default="A1")
    user_id: str = Field(default="user-1")
    amount: float = Field(default=50.0, gt=0)


class CircuitState(str, Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreaker:
    def __init__(self, failure_threshold: int, reset_seconds: float) -> None:
        self.failure_threshold = failure_threshold
        self.reset_seconds = reset_seconds
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.opened_at = 0.0

    def allow_request(self) -> bool:
        if self.state == CircuitState.CLOSED:
            return True
        if self.state == CircuitState.OPEN:
            if time.time() - self.opened_at >= self.reset_seconds:
                self.state = CircuitState.HALF_OPEN
                return True
            return False
        return True

    def record_success(self) -> None:
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.opened_at = 0.0

    def record_failure(self) -> None:
        self.failure_count += 1
        if self.failure_count >= self.failure_threshold or self.state == CircuitState.HALF_OPEN:
            self.state = CircuitState.OPEN
            self.opened_at = time.time()


payment_circuit = CircuitBreaker(
    failure_threshold=PAYMENT_FAILURE_THRESHOLD,
    reset_seconds=PAYMENT_CIRCUIT_RESET_SECONDS,
)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "reservations"}


@app.get("/resilience")
async def resilience_state() -> dict:
    return {
        "payment_circuit": {
            "state": payment_circuit.state,
            "failure_count": payment_circuit.failure_count,
        }
    }


async def reserve_inventory(request: ReservationRequest) -> dict:
    backoffs = [0.2, 0.5, 1.0]
    last_error = "inventory unavailable"

    for attempt in range(INVENTORY_RETRY_ATTEMPTS):
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                response = await client.post(
                    f"{INVENTORY_URL}/inventory/reserve",
                    json=request.model_dump(),
                )
            if response.status_code == 200:
                return response.json()
            last_error = response.text
            if response.status_code in (400, 404, 409):
                try:
                    detail = response.json()
                except ValueError:
                    detail = response.text
                raise HTTPException(
                    status_code=response.status_code,
                    detail={
                        "message": "inventory reservation rejected",
                        "cause": detail,
                    },
                )
        except httpx.HTTPError as exc:
            last_error = str(exc)

        if attempt < len(backoffs):
            await asyncio.sleep(backoffs[attempt])

    raise HTTPException(
        status_code=503,
        detail={"message": "inventory reservation failed", "cause": last_error},
    )


async def release_inventory(request: ReservationRequest) -> None:
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            await client.post(f"{INVENTORY_URL}/inventory/release", json=request.model_dump())
    except httpx.HTTPError:
        # This should be compensated by operational reconciliation in a real system.
        pass


async def charge_payment(request: ReservationRequest, reservation_id: str) -> dict:
    if not payment_circuit.allow_request():
        raise HTTPException(
            status_code=503,
            detail={
                "message": "payment circuit is open",
                "fallback": "reservation rejected before calling payments",
            },
        )

    try:
        async with httpx.AsyncClient(timeout=PAYMENT_TIMEOUT_SECONDS) as client:
            response = await client.post(
                f"{PAYMENTS_URL}/payments/charge",
                json={
                    "reservation_id": reservation_id,
                    "user_id": request.user_id,
                    "amount": request.amount,
                },
            )
        response.raise_for_status()
        payment_circuit.record_success()
        return response.json()
    except (httpx.TimeoutException, httpx.HTTPError) as exc:
        payment_circuit.record_failure()
        raise HTTPException(
            status_code=503,
            detail={
                "message": "payment service unavailable or too slow",
                "circuit_state": payment_circuit.state,
            },
        ) from exc


async def send_notification(request: ReservationRequest, reservation_id: str) -> dict:
    try:
        async with httpx.AsyncClient(timeout=NOTIFICATION_TIMEOUT_SECONDS) as client:
            response = await client.post(
                f"{NOTIFICATIONS_URL}/notifications/send",
                json={
                    "reservation_id": reservation_id,
                    "user_id": request.user_id,
                    "event_id": request.event_id,
                    "seat_id": request.seat_id,
                },
            )
        response.raise_for_status()
        return {"status": "sent"}
    except httpx.HTTPError:
        return {"status": "pending", "reason": "notification service unavailable"}


@app.post("/reservations")
async def create_reservation(request: ReservationRequest) -> dict:
    reservation_id = str(uuid4())

    inventory_result = await reserve_inventory(request)

    try:
        payment_result = await charge_payment(request, reservation_id)
    except HTTPException:
        await release_inventory(request)
        raise

    notification_result = await send_notification(request, reservation_id)

    return {
        "reservation_id": reservation_id,
        "status": "confirmed",
        "inventory": inventory_result,
        "payment": payment_result,
        "notification": notification_result,
    }
