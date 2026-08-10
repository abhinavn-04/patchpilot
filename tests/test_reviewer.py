import asyncio

import pytest

from app.findings import ReviewFinding, Severity
from app.github import ChangedFile, PullRequestContext
from app.reviewer import (
    FakeLLMReviewer,
    LLMReviewRequest,
    ReviewerNotConfiguredError,
    UnconfiguredLLMReviewer,
)


def _review_request() -> LLMReviewRequest:
    return LLMReviewRequest(
        pull_request=PullRequestContext(
            repository="abhinavn-04/patchpilot",
            number=7,
            title="Add review contract",
            head_sha="abc123",
            base_ref="main",
            changed_files=(),
        ),
        changed_files=(
            ChangedFile("app/reviewer.py", "added", 10, 0, 10, "+class Reviewer: ..."),
        ),
        static_findings=(
            ReviewFinding(
                "app/reviewer.py",
                1,
                "python.bare-except",
                "reliability",
                Severity.MEDIUM,
                "Catch a specific exception.",
            ),
        ),
    )


def test_review_request_keeps_bounded_review_context() -> None:
    request = _review_request()

    assert request.pull_request.repository == "abhinavn-04/patchpilot"
    assert request.changed_files[0].filename == "app/reviewer.py"
    assert request.static_findings[0].severity is Severity.MEDIUM


def test_unconfigured_reviewer_never_calls_a_provider() -> None:
    with pytest.raises(ReviewerNotConfiguredError, match="No LLM reviewer is configured"):
        asyncio.run(UnconfiguredLLMReviewer().review(_review_request()))


def test_fake_reviewer_returns_configured_response_and_records_request() -> None:
    request = _review_request()
    reviewer = FakeLLMReviewer('{"findings": [{"rule_id": "demo"}]}')

    response = asyncio.run(reviewer.review(request))

    assert response == '{"findings": [{"rule_id": "demo"}]}'
    assert reviewer.requests == [request]
