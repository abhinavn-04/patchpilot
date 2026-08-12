import asyncio
import json

import httpx
import pytest

from app.findings import Severity
from app.github import GitHubClient, PullRequestContext
from app.llm_findings import LLMFinding
from app.publishing import HIGH_CONFIDENCE_THRESHOLD, publish_high_confidence_findings


def _pull_request() -> PullRequestContext:
    return PullRequestContext("acme/patchpilot", 42, "Review me", "head-sha", "main", ())


def _finding(title: str, confidence: float) -> LLMFinding:
    return LLMFinding(
        "app/service.py",
        12,
        Severity.HIGH,
        confidence,
        title,
        "Validate the request before processing it.",
    )


def test_publish_high_confidence_findings_posts_only_qualified_findings() -> None:
    requests: list[httpx.Request] = []

    async def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(201, json={"id": 314})

    async def publish():
        client = GitHubClient("test-token", transport=httpx.MockTransport(handler))
        try:
            return await publish_high_confidence_findings(
                client=client,
                pull_request=_pull_request(),
                findings=(_finding("Low confidence", 0.79), _finding("Validate input", 0.91)),
            )
        finally:
            await client.aclose()

    published = asyncio.run(publish())

    assert [comment.finding.title for comment in published] == ["Validate input"]
    assert published[0].github_comment_id == 314
    assert len(requests) == 1
    assert requests[0].method == "POST"
    assert requests[0].url.path == "/repos/acme/patchpilot/pulls/42/comments"
    assert json.loads(requests[0].content) == {
        "body": "**[HIGH] Validate input** (confidence: 91%)\n\nValidate the request before processing it.",
        "commit_id": "head-sha",
        "path": "app/service.py",
        "line": 12,
        "side": "RIGHT",
    }


def test_publish_high_confidence_findings_rejects_invalid_threshold() -> None:
    async def publish() -> None:
        client = GitHubClient("test-token", transport=httpx.MockTransport(lambda _: None))
        try:
            await publish_high_confidence_findings(
                client=client,
                pull_request=_pull_request(),
                findings=(),
                minimum_confidence=1.1,
            )
        finally:
            await client.aclose()

    with pytest.raises(ValueError, match="between 0 and 1"):
        asyncio.run(publish())


def test_default_threshold_is_high_confidence() -> None:
    assert HIGH_CONFIDENCE_THRESHOLD == 0.80
