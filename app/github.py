"""Typed GitHub REST client for pull-request review data."""

from dataclasses import dataclass

import httpx


@dataclass(frozen=True)
class ChangedFile:
    """A single changed file returned by GitHub's pull-request API."""

    filename: str
    status: str
    additions: int
    deletions: int
    changes: int
    patch: str | None


@dataclass(frozen=True)
class PullRequestContext:
    """Pull-request metadata and every changed file needed for review."""

    repository: str
    number: int
    title: str
    head_sha: str
    base_ref: str
    changed_files: tuple[ChangedFile, ...]


class GitHubClient:
    """Small asynchronous client for the GitHub pull-request REST API."""

    def __init__(
        self,
        token: str,
        *,
        base_url: str = "https://api.github.com",
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self._client = httpx.AsyncClient(
            base_url=base_url,
            headers={
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {token}",
                "X-GitHub-Api-Version": "2022-11-28",
            },
            timeout=10.0,
            transport=transport,
        )

    async def aclose(self) -> None:
        """Release HTTP resources held by the client."""
        await self._client.aclose()

    async def fetch_pull_request_context(
        self, *, repository: str, pull_number: int
    ) -> PullRequestContext:
        """Fetch pull-request metadata and all changed files."""
        pull_request = await self._get_json(f"/repos/{repository}/pulls/{pull_number}")
        changed_files = await self._fetch_changed_files(repository, pull_number)

        return PullRequestContext(
            repository=repository,
            number=pull_number,
            title=pull_request["title"],
            head_sha=pull_request["head"]["sha"],
            base_ref=pull_request["base"]["ref"],
            changed_files=tuple(changed_files),
        )

    async def create_pull_request_review_comment(
        self,
        *,
        repository: str,
        pull_number: int,
        commit_sha: str,
        filename: str,
        line: int,
        body: str,
    ) -> int:
        """Create a line-level review comment and return its GitHub comment ID."""
        response = await self._client.post(
            f"/repos/{repository}/pulls/{pull_number}/comments",
            json={
                "body": body,
                "commit_id": commit_sha,
                "path": filename,
                "line": line,
                "side": "RIGHT",
            },
        )
        response.raise_for_status()
        return int(response.json()["id"])

    async def _fetch_changed_files(
        self, repository: str, pull_number: int
    ) -> list[ChangedFile]:
        next_url: str | None = f"/repos/{repository}/pulls/{pull_number}/files?per_page=100"
        changed_files: list[ChangedFile] = []

        while next_url:
            response = await self._client.get(next_url)
            response.raise_for_status()
            changed_files.extend(
                ChangedFile(
                    filename=file["filename"],
                    status=file["status"],
                    additions=file["additions"],
                    deletions=file["deletions"],
                    changes=file["changes"],
                    patch=file.get("patch"),
                )
                for file in response.json()
            )
            next_link = response.links.get("next")
            next_url = next_link["url"] if next_link else None

        return changed_files

    async def _get_json(self, url: str) -> dict:
        response = await self._client.get(url)
        response.raise_for_status()
        return response.json()
