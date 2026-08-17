"""Publish high-confidence LLM findings as GitHub pull-request comments."""

from dataclasses import dataclass

from app.github import GitHubClient, PullRequestContext
from app.llm_findings import LLMFinding
from app.ranking import deduplicate_and_rank_llm_findings

HIGH_CONFIDENCE_THRESHOLD = 0.80


@dataclass(frozen=True)
class PublishedReviewComment:
    """A finding successfully posted to a GitHub pull request."""

    finding: LLMFinding
    github_comment_id: int


async def publish_high_confidence_findings(
    *,
    client: GitHubClient,
    pull_request: PullRequestContext,
    findings: tuple[LLMFinding, ...],
    minimum_confidence: float = HIGH_CONFIDENCE_THRESHOLD,
) -> tuple[PublishedReviewComment, ...]:
    """Rank, filter, and post only sufficiently confident findings."""
    if not 0 <= minimum_confidence <= 1:
        raise ValueError("minimum_confidence must be between 0 and 1.")

    published: list[PublishedReviewComment] = []
    for finding in deduplicate_and_rank_llm_findings(findings):
        if finding.confidence < minimum_confidence:
            continue
        comment_id = await client.create_pull_request_review_comment(
            repository=pull_request.repository,
            pull_number=pull_request.number,
            commit_sha=pull_request.head_sha,
            filename=finding.filename,
            line=finding.line,
            body=_format_comment(finding),
        )
        published.append(PublishedReviewComment(finding, comment_id))
    return tuple(published)


def _format_comment(finding: LLMFinding) -> str:
    percentage = round(finding.confidence * 100)
    return (
        f"**[{finding.severity.upper()}] {finding.title}** (confidence: {percentage}%)\n\n"
        f"{finding.message}"
    )
