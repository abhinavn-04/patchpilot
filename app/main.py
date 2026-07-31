"""HTTP entry point for PatchPilot."""

import os
from typing import Annotated

from fastapi import FastAPI, Header, HTTPException, Request, status

from app.webhooks import verify_github_signature

app = FastAPI(
    title="PatchPilot",
    version="0.1.0",
    description="AI-assisted GitHub pull-request review service.",
)


@app.get("/health", tags=["operations"])
async def health_check() -> dict[str, str]:
    """Report that the HTTP process is running."""
    return {"status": "ok"}


@app.get("/ready", tags=["operations"])
async def readiness_check() -> dict[str, str]:
    """Report readiness to accept review work.

    Dependency checks will be added alongside PostgreSQL and Redis integration.
    """
    return {"status": "ready"}


@app.post("/webhooks/github", status_code=status.HTTP_202_ACCEPTED, tags=["webhooks"])
async def receive_github_webhook(
    request: Request,
    x_hub_signature_256: Annotated[str | None, Header()] = None,
) -> dict[str, str]:
    """Accept a GitHub delivery only after its signature is verified."""
    webhook_secret = os.getenv("GITHUB_WEBHOOK_SECRET")
    if not webhook_secret:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="GitHub webhook secret is not configured.",
        )

    if not verify_github_signature(
        payload=await request.body(),
        signature=x_hub_signature_256,
        secret=webhook_secret,
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="GitHub webhook signature is invalid.",
        )

    return {"status": "accepted"}
