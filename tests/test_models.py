from sqlalchemy import create_engine
from sqlalchemy.dialects import postgresql
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from sqlalchemy.schema import CreateTable

from app.models import Base, PullRequestReview, ReviewStatus


def build_review(**overrides: object) -> PullRequestReview:
    values: dict[str, object] = {
        "repository_full_name": "abhinavn-04/patchpilot",
        "pull_number": 12,
        "head_sha": "a" * 40,
    }
    values.update(overrides)
    return PullRequestReview(**values)  # type: ignore[arg-type]


def test_review_job_defaults_to_queued_and_persists() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        review = build_review()
        session.add(review)
        session.commit()

        assert review.id is not None
        assert review.status is ReviewStatus.QUEUED


def test_review_job_rejects_duplicate_repository_pull_and_commit() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        session.add(build_review())
        session.commit()

        session.add(build_review())
        try:
            session.commit()
        except IntegrityError:
            session.rollback()
        else:
            raise AssertionError("duplicate review job should violate the unique constraint")


def test_review_job_table_compiles_for_postgresql() -> None:
    ddl = str(
        CreateTable(PullRequestReview.__table__).compile(dialect=postgresql.dialect())
    )

    assert "pull_request_reviews" in ddl
    assert "review_status" in ddl
