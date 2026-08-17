"""Conservative secret redaction for content sent to external LLM providers."""

import re

from app.github import ChangedFile
from app.reviewer import LLMReviewer, LLMReviewRequest

_REDACTED = "[REDACTED]"
_ASSIGNMENT = re.compile(
    r"(?im)(\b(?:api[_-]?key|access[_-]?token|auth[_-]?token|password|passwd|secret|token)\b\s*[:=]\s*)(?:\"[^\"]*\"|'[^']*'|[^\s,;]+)"
)
_BEARER_TOKEN = re.compile(r"(?i)(\bBearer\s+)[A-Za-z0-9._~+/-]+")
_GITHUB_TOKEN = re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b")
_AWS_ACCESS_KEY = re.compile(r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b")
_PRIVATE_KEY = re.compile(
    r"-----BEGIN (?:[A-Z ]+ )?PRIVATE KEY-----.*?-----END (?:[A-Z ]+ )?PRIVATE KEY-----",
    re.DOTALL,
)


def redact_text(value: str) -> str:
    """Replace common credential formats with a stable placeholder."""
    redacted = _PRIVATE_KEY.sub(_REDACTED, value)
    redacted = _ASSIGNMENT.sub(rf"\1{_REDACTED}", redacted)
    redacted = _BEARER_TOKEN.sub(rf"\1{_REDACTED}", redacted)
    redacted = _GITHUB_TOKEN.sub(_REDACTED, redacted)
    return _AWS_ACCESS_KEY.sub(_REDACTED, redacted)


def redact_review_request(request: LLMReviewRequest) -> LLMReviewRequest:
    """Return an LLM request with likely secrets removed from user-controlled text."""
    return LLMReviewRequest(
        pull_request=request.pull_request.__class__(
            repository=request.pull_request.repository,
            number=request.pull_request.number,
            title=redact_text(request.pull_request.title),
            head_sha=request.pull_request.head_sha,
            base_ref=request.pull_request.base_ref,
            changed_files=request.pull_request.changed_files,
        ),
        changed_files=tuple(
            ChangedFile(
                filename=file.filename,
                status=file.status,
                additions=file.additions,
                deletions=file.deletions,
                changes=file.changes,
                patch=redact_text(file.patch) if file.patch is not None else None,
            )
            for file in request.changed_files
        ),
        static_findings=request.static_findings,
    )


class RedactingLLMReviewer:
    """Sanitize review content before passing it to an external provider adapter."""

    def __init__(self, reviewer: LLMReviewer) -> None:
        self._reviewer = reviewer

    async def review(self, request: LLMReviewRequest) -> str:
        return await self._reviewer.review(redact_review_request(request))
