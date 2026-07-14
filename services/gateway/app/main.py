import os
import time
from collections import defaultdict, deque

import httpx
from fastapi import FastAPI, HTTPException, Request


RESERVATIONS_URL = os.getenv("RESERVATIONS_URL", "http://localhost:8001")
RATE_LIMIT_REQUESTS = int(os.getenv("RATE_LIMIT_REQUESTS", "30"))
RATE_LIMIT_WINDOW_SECONDS = int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "10"))

app = FastAPI(title="Ticket API Gateway", version="0.1.0")
request_log: dict[str, deque[float]] = defaultdict(deque)


def enforce_rate_limit(client_id: str) -> None:
    now = time.time()
    window_start = now - RATE_LIMIT_WINDOW_SECONDS
    history = request_log[client_id]

    while history and history[0] < window_start:
        history.popleft()

    if len(history) >= RATE_LIMIT_REQUESTS:
        raise HTTPException(
            status_code=429,
            detail="Too many requests. Please retry later.",
        )

    history.append(now)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "gateway"}


@app.post("/reserve")
async def reserve_ticket(payload: dict, request: Request) -> dict:
    client_id = request.client.host if request.client else "unknown"
    enforce_rate_limit(client_id)

    try:
        async with httpx.AsyncClient(timeout=6.0) as client:
            response = await client.post(f"{RESERVATIONS_URL}/reservations", json=payload)
    except httpx.TimeoutException as exc:
        raise HTTPException(status_code=504, detail="Reservations service timed out") from exc
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=503, detail="Reservations service unavailable") from exc

    if response.status_code >= 400:
        raise HTTPException(status_code=response.status_code, detail=response.json())

    return response.json()
