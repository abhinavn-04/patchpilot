from datetime import datetime, timezone
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import get_session
from app.main import app
from app.models import Base, PullRequestReview, ReviewStatus

client = TestClient(app)


@pytest.fixture
def review_database():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, expire_on_commit=False)

    def override_get_session():
        with session_factory() as session:
            yield session

    app.dependency_overrides[get_session] = override_get_session
    yield session_factory
    app.dependency_overrides.clear()
    Base.metadata.drop_all(engine)
    engine.dispose()


def test_review_summary_returns_persisted_status_and_summary(review_database) -> None:
    completed_at = datetime.now(timezone.utc)
    with review_database() as session:
        review = PullRequestReview(
            repository_full_name="acme/patchpilot",
            pull_number=42,
            head_sha="a" * 40,
            status=ReviewStatus.COMPLETED,
            summary="Published 2 high-confidence findings.",
            completed_at=completed_at,
        )
        session.add(review)
        session.commit()
        review_id = review.id

    response = client.get(f"/reviews/{review_id}")

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == str(review_id)
    assert body["repository"] == "acme/patchpilot"
    assert body["pull_number"] == 42
    assert body["head_sha"] == "a" * 40
    assert body["status"] == "completed"
    assert body["summary"] == "Published 2 high-confidence findings."
    assert datetime.fromisoformat(body["completed_at"]).replace(tzinfo=timezone.utc) == completed_at
    assert body["created_at"]
    assert body["updated_at"]


def test_review_summary_returns_404_for_unknown_review(review_database) -> None:
    response = client.get(f"/reviews/{uuid4()}")

    assert response.status_code == 404
    assert response.json() == {"detail": "Review job was not found."}
