import asyncio
import os
import random

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel


NOTIFICATION_DELAY_MS = int(os.getenv("NOTIFICATION_DELAY_MS", "150"))
NOTIFICATION_FAILURE_RATE = float(os.getenv("NOTIFICATION_FAILURE_RATE", "0.0"))

app = FastAPI(title="Notifications Stub Service", version="0.1.0")


class NotificationRequest(BaseModel):
    reservation_id: str
    user_id: str
    event_id: str
    seat_id: str


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "notifications"}


@app.post("/notifications/send")
async def send_notification(request: NotificationRequest) -> dict:
    await asyncio.sleep(NOTIFICATION_DELAY_MS / 1000)

    if random.random() < NOTIFICATION_FAILURE_RATE:
        raise HTTPException(status_code=503, detail="simulated notification failure")

    return {
        "status": "sent",
        "reservation_id": request.reservation_id,
        "channel": "email",
    }
