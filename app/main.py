"""HTTP entry point for PatchPilot."""

import os
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import Depends, FastAPI, Header, HTTPException, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_session, initialize_database
from app.deliveries import record_webhook_delivery
from app.models import PullRequestReview, ReviewStatus
from app.reviews import queue_pull_request_review
from app.webhooks import verify_github_signature


@asynccontextmanager
async def lifespan(_: FastAPI):
    initialize_database()
    yield


app = FastAPI(
    title="PatchPilot",
    version="0.1.0",
    description="AI-assisted GitHub pull-request review service.",
    lifespan=lifespan,
)


class ReviewSummaryResponse(BaseModel):
    """Safe, durable status information for a pull-request review job."""

    id: UUID
    repository: str
    pull_number: int
    head_sha: str
    status: ReviewStatus
    summary: str | None
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime


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


@app.get("/reviews/{review_id}", response_model=ReviewSummaryResponse, tags=["reviews"])
def get_review_summary(
    review_id: UUID,
    session: Session = Depends(get_session),
) -> ReviewSummaryResponse:
    """Return the durable status and summary for one pull-request review job."""
    review = session.get(PullRequestReview, review_id)
    if review is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review job was not found.",
        )

    return ReviewSummaryResponse(
        id=review.id,
        repository=review.repository_full_name,
        pull_number=review.pull_number,
        head_sha=review.head_sha,
        status=review.status,
        summary=review.summary,
        completed_at=review.completed_at,
        created_at=review.created_at,
        updated_at=review.updated_at,
    )


@app.post("/webhooks/github", status_code=status.HTTP_202_ACCEPTED, tags=["webhooks"])
async def receive_github_webhook(
    request: Request,
    x_hub_signature_256: Annotated[str | None, Header()] = None,
    x_github_delivery: Annotated[str | None, Header()] = None,
    x_github_event: Annotated[str | None, Header()] = None,
    session: Session = Depends(get_session),
) -> JSONResponse:
    """Accept a GitHub delivery only after its signature is verified."""
    webhook_secret = os.getenv("GITHUB_WEBHOOK_SECRET")
    if not webhook_secret:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="GitHub webhook secret is not configured.",
        )

    payload = await request.body()
    if not verify_github_signature(
        payload=payload,
        signature=x_hub_signature_256,
        secret=webhook_secret,
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="GitHub webhook signature is invalid.",
        )

    if not x_github_delivery or not x_github_event:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="GitHub delivery and event headers are required.",
        )

    is_new_delivery = record_webhook_delivery(
        session,
        delivery_id=x_github_delivery,
        event_name=x_github_event,
        payload=payload,
    )
    if not is_new_delivery:
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"status": "duplicate", "delivery_id": x_github_delivery},
        )

    queue_pull_request_review(
        session,
        event_name=x_github_event,
        payload=payload,
    )

    return JSONResponse(
        status_code=status.HTTP_202_ACCEPTED,
        content={"status": "accepted", "delivery_id": x_github_delivery},
    )
