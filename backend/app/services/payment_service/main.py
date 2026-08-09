"""Simulated Payment API Microservice for production failure testing."""

from __future__ import annotations

import traceback
from typing import Any
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field

from app.services.payment_service.failure_injector import FailureMode, injector
from app.services.payment_service.logger import log_payment_event

app = FastAPI(
    title="Simulated Payment API",
    description="Microservice simulating payment processing with controlled failure injection for AI incident testing.",
    version="1.0.0",
)


class PaymentRequest(BaseModel):
    amount: float = Field(gt=0, examples=[99.99])
    currency: str = Field(default="USD", examples=["USD"])
    customer_id: str = Field(examples=["cust_12345"])


class FailureSimulationRequest(BaseModel):
    mode: FailureMode
    failure_rate: float = Field(default=1.0, ge=0.0, le=1.0)


@app.get("/health", tags=["system"])
async def health() -> dict[str, Any]:
    return {"status": "ok", "service": "payment-api", "active_failure_mode": injector.active_mode.value}


@app.post("/simulate-failure", tags=["control"])
async def set_failure_mode(req: FailureSimulationRequest) -> dict[str, Any]:
    """Inject a production failure mode into the Payment API."""
    injector.set_mode(req.mode, req.failure_rate)
    log_payment_event(
        severity="WARNING",
        message=f"Failure injection mode updated to '{req.mode.value}' with rate {req.failure_rate}",
        metadata={"mode": req.mode.value},
    )
    return {"message": f"Failure mode set to {req.mode.value}", "rate": req.failure_rate}


@app.post("/clear-failures", tags=["control"])
async def clear_failures() -> dict[str, str]:
    injector.clear()
    return {"message": "Failure modes cleared"}


@app.post("/pay", tags=["payments"])
async def process_payment(req: PaymentRequest) -> dict[str, Any]:
    """Process a payment request."""
    try:
        await injector.execute_injection()
        
        log_payment_event(
            severity="INFO",
            message=f"Payment processed successfully for customer '{req.customer_id}' (${req.amount})",
            metadata={"amount": req.amount, "currency": req.currency, "customer_id": req.customer_id},
        )
        return {
            "status": "success",
            "transaction_id": f"txn_{req.customer_id[:5]}_99",
            "amount": req.amount,
            "currency": req.currency,
        }

    except Exception as e:
        tb = traceback.format_exc()
        severity = "CRITICAL" if isinstance(e, (TimeoutError, MemoryError)) else "ERROR"
        
        log_payment_event(
            severity=severity,
            message=str(e),
            metadata={"customer_id": req.customer_id, "amount": req.amount},
            stack_trace=tb,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Payment Processing Error: {e}",
        )
