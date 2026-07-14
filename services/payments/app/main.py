import asyncio
import os
import random
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field


PAYMENT_DELAY_MS = int(os.getenv("PAYMENT_DELAY_MS", "250"))
PAYMENT_FAILURE_RATE = float(os.getenv("PAYMENT_FAILURE_RATE", "0.0"))

app = FastAPI(title="Payments Stub Service", version="0.1.0")


class PaymentRequest(BaseModel):
    reservation_id: str
    user_id: str
    amount: float = Field(gt=0)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "payments"}


@app.post("/payments/charge")
async def charge(request: PaymentRequest) -> dict:
    await asyncio.sleep(PAYMENT_DELAY_MS / 1000)

    if random.random() < PAYMENT_FAILURE_RATE:
        raise HTTPException(status_code=503, detail="simulated payment processor failure")

    return {
        "status": "charged",
        "transaction_id": str(uuid4()),
        "reservation_id": request.reservation_id,
        "amount": request.amount,
    }
