"""Provider-independent contract for AI-assisted pull-request review."""

from dataclasses import dataclass
from typing import Protocol

from app.findings import ReviewFinding
from app.github import ChangedFile, PullRequestContext


@dataclass(frozen=True)
class LLMReviewRequest:
    """The bounded pull-request context sent to an LLM reviewer."""

    pull_request: PullRequestContext
    changed_files: tuple[ChangedFile, ...]
    static_findings: tuple[ReviewFinding, ...]


class LLMReviewer(Protocol):
    """An asynchronous provider adapter that reviews one pull request."""

    async def review(self, request: LLMReviewRequest) -> str:
        """Return the provider's raw review response for the supplied context."""


class ReviewerNotConfiguredError(RuntimeError):
    """Raised when a review is requested before a provider adapter is configured."""


class UnconfiguredLLMReviewer:
    """Safe default that prevents an accidental provider or network call."""

    async def review(self, request: LLMReviewRequest) -> str:
        del request
        raise ReviewerNotConfiguredError(
            "No LLM reviewer is configured. Install a provider adapter before requesting AI review."
        )
