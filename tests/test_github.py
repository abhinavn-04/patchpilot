import asyncio
import json

import httpx
import pytest

from app.github import GitHubClient


def test_client_fetches_pull_request_metadata_and_all_changed_files() -> None:
    requested_urls: list[str] = []

    async def handler(request: httpx.Request) -> httpx.Response:
        requested_urls.append(str(request.url))
        assert request.headers["Authorization"] == "Bearer test-token"

        if request.url.path == "/repos/acme/patchpilot/pulls/42":
            return httpx.Response(
                200,
                json={
                    "title": "Add webhook handling",
                    "head": {"sha": "head-sha"},
                    "base": {"ref": "main"},
                },
            )
        if request.url.params.get("page") == "2":
            return httpx.Response(
                200,
                json=[
                    {
                        "filename": "tests/test_webhooks.py",
                        "status": "added",
                        "additions": 20,
                        "deletions": 0,
                        "changes": 20,
                    }
                ],
            )
        return httpx.Response(
            200,
            headers={
                "Link": (
                    "<https://api.github.com/repos/acme/patchpilot/pulls/42/files?"
                    "page=2&per_page=100>; "
                    'rel="next"'
                )
            },
            json=[
                {
                    "filename": "app/webhooks.py",
                    "status": "modified",
                    "additions": 12,
                    "deletions": 2,
                    "changes": 14,
                    "patch": "@@ -1 +1 @@",
                }
            ],
        )

    async def fetch_context():
        client = GitHubClient("test-token", transport=httpx.MockTransport(handler))
        try:
            return await client.fetch_pull_request_context(
                repository="acme/patchpilot", pull_number=42
            )
        finally:
            await client.aclose()

    context = asyncio.run(fetch_context())

    assert context.title == "Add webhook handling"
    assert context.head_sha == "head-sha"
    assert context.base_ref == "main"
    assert [file.filename for file in context.changed_files] == [
        "app/webhooks.py",
        "tests/test_webhooks.py",
    ]
    assert context.changed_files[0].patch == "@@ -1 +1 @@"
    assert context.changed_files[1].patch is None
    assert len(requested_urls) == 3


def test_client_propagates_github_api_errors() -> None:
    async def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(404, json={"message": "Not Found"})

    async def fetch_missing_pull_request() -> None:
        client = GitHubClient("test-token", transport=httpx.MockTransport(handler))
        try:
            await client.fetch_pull_request_context(repository="acme/patchpilot", pull_number=42)
        finally:
            await client.aclose()

    with pytest.raises(httpx.HTTPStatusError):
        asyncio.run(fetch_missing_pull_request())


def test_client_posts_line_level_pull_request_review_comment() -> None:
    requests: list[httpx.Request] = []

    async def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(201, json={"id": 987})

    async def create_comment() -> int:
        client = GitHubClient("test-token", transport=httpx.MockTransport(handler))
        try:
            return await client.create_pull_request_review_comment(
                repository="acme/patchpilot",
                pull_number=42,
                commit_sha="head-sha",
                filename="app/service.py",
                line=12,
                body="Review comment",
            )
        finally:
            await client.aclose()

    assert asyncio.run(create_comment()) == 987
    assert len(requests) == 1
    assert requests[0].method == "POST"
    assert requests[0].url.path == "/repos/acme/patchpilot/pulls/42/comments"
    assert requests[0].headers["Authorization"] == "Bearer test-token"
    assert json.loads(requests[0].content) == {
        "body": "Review comment",
        "commit_id": "head-sha",
        "path": "app/service.py",
        "line": 12,
        "side": "RIGHT",
    }


def test_client_propagates_review_comment_api_errors() -> None:
    async def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(422, json={"message": "Line must be part of the diff"})

    async def create_comment() -> None:
        client = GitHubClient("test-token", transport=httpx.MockTransport(handler))
        try:
            await client.create_pull_request_review_comment(
                repository="acme/patchpilot",
                pull_number=42,
                commit_sha="head-sha",
                filename="app/service.py",
                line=12,
                body="Review comment",
            )
        finally:
            await client.aclose()

    with pytest.raises(httpx.HTTPStatusError):
        asyncio.run(create_comment())
