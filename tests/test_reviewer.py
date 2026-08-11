import asyncio

import pytest

from app.findings import ReviewFinding, Severity
from app.github import ChangedFile, PullRequestContext
from app.redaction import RedactingLLMReviewer, redact_review_request, redact_text
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


def test_redact_text_replaces_common_secret_formats() -> None:
    value = """token = \"top-secret\"
Authorization: Bearer bearer-token-value
github = ghp_abcdefghijklmnopqrstuvwxyz123456
aws = AKIA1234567890ABCDEF
-----BEGIN PRIVATE KEY-----
private-key-content
-----END PRIVATE KEY-----"""

    redacted = redact_text(value)

    assert "top-secret" not in redacted
    assert "bearer-token-value" not in redacted
    assert "ghp_abcdefghijklmnopqrstuvwxyz123456" not in redacted
    assert "AKIA1234567890ABCDEF" not in redacted
    assert "private-key-content" not in redacted
    assert redacted.count("[REDACTED]") == 5


def test_redact_review_request_returns_sanitized_copy() -> None:
    request = _review_request()
    request = LLMReviewRequest(
        pull_request=PullRequestContext(
            repository=request.pull_request.repository,
            number=request.pull_request.number,
            title="Fix password = \"do-not-send\"",
            head_sha=request.pull_request.head_sha,
            base_ref=request.pull_request.base_ref,
            changed_files=request.pull_request.changed_files,
        ),
        changed_files=(
            ChangedFile("app/config.py", "modified", 1, 1, 2, '+api_key = "do-not-send"'),
        ),
        static_findings=request.static_findings,
    )

    redacted = redact_review_request(request)

    assert redacted is not request
    assert redacted.pull_request.title == "Fix password = [REDACTED]"
    assert redacted.changed_files[0].patch == "+api_key = [REDACTED]"
    assert request.pull_request.title == "Fix password = \"do-not-send\""
    assert request.changed_files[0].patch == '+api_key = "do-not-send"'


def test_redacting_reviewer_sanitizes_content_before_calling_provider() -> None:
    request = _review_request()
    request = LLMReviewRequest(
        pull_request=request.pull_request,
        changed_files=(
            ChangedFile("app/config.py", "modified", 1, 1, 2, '+token = "do-not-send"'),
        ),
        static_findings=request.static_findings,
    )
    provider = FakeLLMReviewer()

    asyncio.run(RedactingLLMReviewer(provider).review(request))

    assert provider.requests[0].changed_files[0].patch == "+token = [REDACTED]"
    assert request.changed_files[0].patch == '+token = "do-not-send"'
