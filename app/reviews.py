"""Create durable review jobs from verified GitHub webhook payloads."""

import json

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import PullRequestReview

_REVIEW_ACTIONS = {"opened", "reopened", "synchronize"}


def queue_pull_request_review(
    session: Session, *, event_name: str, payload: bytes
) -> PullRequestReview | None:
    """Queue one review per pull-request commit for supported GitHub actions."""
    if event_name != "pull_request":
        return None

    try:
        data = json.loads(payload)
        if data.get("action") not in _REVIEW_ACTIONS:
            return None
        repository = data["repository"]["full_name"]
        pull_number = data["number"]
        head_sha = data["pull_request"]["head"]["sha"]
    except (json.JSONDecodeError, KeyError, TypeError):
        return None

    if (
        not isinstance(repository, str)
        or not repository
        or not isinstance(pull_number, int)
        or isinstance(pull_number, bool)
        or pull_number < 1
        or not isinstance(head_sha, str)
        or not head_sha
    ):
        return None

    review = PullRequestReview(
        repository_full_name=repository,
        pull_number=pull_number,
        head_sha=head_sha,
    )
    session.add(review)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        return session.scalar(
            select(PullRequestReview).where(
                PullRequestReview.repository_full_name == repository,
                PullRequestReview.pull_number == pull_number,
                PullRequestReview.head_sha == head_sha,
            )
        )
    return review
