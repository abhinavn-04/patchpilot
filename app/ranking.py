"""Deterministic deduplication and ranking for validated LLM findings."""

from app.findings import Severity
from app.llm_findings import LLMFinding

_SEVERITY_RANK = {
    Severity.HIGH: 3,
    Severity.MEDIUM: 2,
    Severity.LOW: 1,
}


def deduplicate_and_rank_llm_findings(
    findings: tuple[LLMFinding, ...],
) -> tuple[LLMFinding, ...]:
    """Keep the strongest duplicate and sort findings for feedback publishing."""
    best_by_key: dict[tuple[str, int, str], LLMFinding] = {}

    for finding in findings:
        key = (finding.filename, finding.line, _normalized_title(finding.title))
        current = best_by_key.get(key)
        if current is None or _precedes(finding, current):
            best_by_key[key] = finding

    return tuple(
        sorted(
            best_by_key.values(),
            key=lambda finding: (
                -finding.confidence,
                -_SEVERITY_RANK[finding.severity],
                finding.filename,
                finding.line,
                _normalized_title(finding.title),
            ),
        )
    )


def _normalized_title(title: str) -> str:
    return " ".join(title.split()).casefold()


def _precedes(candidate: LLMFinding, current: LLMFinding) -> bool:
    """Return whether a duplicate candidate should replace the stored finding."""
    candidate_key = (
        candidate.confidence,
        _SEVERITY_RANK[candidate.severity],
        candidate.message.casefold(),
    )
    current_key = (
        current.confidence,
        _SEVERITY_RANK[current.severity],
        current.message.casefold(),
    )
    return candidate_key > current_key
