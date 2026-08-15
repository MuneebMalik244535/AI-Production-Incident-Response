"""Standalone Target E-Commerce Application (Port 5000)

This is a completely independent microservice simulating an E-Commerce Checkout API.
When errors or outages occur here, it dispatches live Webhook payloads to the
AI Production Incident Response Platform (Port 8000).
"""

from __future__ import annotations

import logging
from typing import Any
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import httpx
import uvicorn

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("target-ecommerce-app")

app = FastAPI(
    title="Standalone Target E-Commerce App",
    description="Independent target service for AI Incident Response testing",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# AI Incident Platform Webhook Endpoint
INCIDENT_PLATFORM_WEBHOOK = "http://localhost:8000/api/incidents"

# State
active_error_state: str = "NONE"


@app.get("/")
def read_root():
    return {
        "service": "ecommerce-checkout-api",
        "status": "healthy" if active_error_state == "NONE" else "DEGRADED",
        "active_error": active_error_state,
        "message": "Standalone Target Application running on Port 5000",
    }


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "ecommerce-checkout-api", "port": 5000}


@app.post("/checkout")
async def process_checkout(payload: dict[str, Any] | None = None):
    """Simulate processing a customer checkout transaction."""
    global active_error_state

    if active_error_state == "DB_TIMEOUT":
        logger.error("❌ Exception in /checkout: sqlalchemy.exc.TimeoutError: QueuePool limit of size 10 overflow 10 reached")
        raise HTTPException(
            status_code=500,
            detail="sqlalchemy.exc.TimeoutError: QueuePool limit of size 10 overflow 10 reached, connection timed out, timeout 30.00",
        )
    elif active_error_state == "API_500":
        logger.error("❌ Exception in /checkout: Upstream payment gateway HTTP 500 Internal Server Error")
        raise HTTPException(
            status_code=500,
            detail="HTTP 500 Internal Server Error: Upstream payment gateway /v2/charge responded with error",
        )
    elif active_error_state == "AUTH_FAIL":
        logger.error("❌ Exception in /checkout: JWT Signature verification failed")
        raise HTTPException(
            status_code=403,
            detail="JWT Signature verification failed: auth token key expired on /v2/checkout",
        )

    return {
        "status": "SUCCESS",
        "order_id": "ORD-98421",
        "amount": 149.99,
        "message": "Payment processed successfully",
    }


@app.post("/trigger-outage")
async def trigger_outage(error_type: str = "db"):
    """Trigger an outage on this service AND notify the AI Incident Response Platform via Webhook."""
    global active_error_state

    error_map = {
        "db": ("DB_TIMEOUT", "sqlalchemy.exc.TimeoutError: QueuePool limit of size 10 overflow 10 reached", "postgres-primary", "CRITICAL"),
        "api": ("API_500", "HTTP 500 Internal Server Error spike - 847 errors/min on /checkout endpoint", "api-gateway", "HIGH"),
        "auth": ("AUTH_FAIL", "JWT verification failed: signature has expired on /v2/login", "auth-service", "CRITICAL"),
    }

    mode, error_msg, service_name, severity = error_map.get(error_type.lower(), error_map["db"])
    active_error_state = mode

    logger.info(f"💥 OUTAGE TRIGGERED on Target App: {mode} ({error_msg})")

    # Send Webhook payload to AI Incident Platform (Port 8000)
    webhook_payload = {
        "service": service_name,
        "error": error_msg,
        "severity": severity,
        "metadata": {
            "source": "standalone-target-ecommerce-app",
            "port": 5000,
            "injected_error": mode,
        },
    }

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            res = await client.post(INCIDENT_PLATFORM_WEBHOOK, json=webhook_payload)
            logger.info(f"📡 Webhook sent to AI Incident Platform (Status: {res.status_code})")
            return {
                "message": f"Outage '{mode}' triggered on Target App (Port 5000)",
                "webhook_status": res.status_code,
                "incident_response": res.json() if res.status_code in (200, 201) else None,
            }
    except Exception as e:
        logger.warning(f"Failed to deliver webhook to AI Incident Platform: {e}")
        return {
            "message": f"Outage '{mode}' active on Target App, but webhook delivery failed ({e})",
            "webhook_status": "FAILED",
        }


@app.post("/reset")
def reset_service():
    """Reset target app back to healthy state."""
    global active_error_state
    active_error_state = "NONE"
    logger.info("✅ Target E-Commerce App reset to HEALTHY state.")
    return {"status": "HEALTHY", "message": "Target app error state cleared"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=5000, reload=True)
