"""Database models for durable pull-request review work."""

from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, DateTime, Enum as SqlEnum, String, Text, UniqueConstraint, Uuid, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for PatchPilot persistence models."""


class ReviewStatus(str, Enum):
    """Lifecycle states for a pull-request review job."""

    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class PullRequestReview(Base):
    """A durable request to review a specific pull-request commit."""

    __tablename__ = "pull_request_reviews"
    __table_args__ = (
        CheckConstraint("pull_number > 0", name="ck_review_pull_number_positive"),
        UniqueConstraint(
            "repository_full_name",
            "pull_number",
            "head_sha",
            name="uq_review_repository_pull_sha",
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    repository_full_name: Mapped[str] = mapped_column(String(255), index=True)
    pull_number: Mapped[int]
    head_sha: Mapped[str] = mapped_column(String(64))
    status: Mapped[ReviewStatus] = mapped_column(
        SqlEnum(ReviewStatus, name="review_status"),
        default=ReviewStatus.QUEUED,
        index=True,
    )
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
