from app.findings import Severity
from app.llm_findings import LLMFinding
from app.ranking import deduplicate_and_rank_llm_findings


def _finding(
    *,
    title: str,
    confidence: float,
    severity: Severity = Severity.LOW,
    filename: str = "app/service.py",
    line: int = 12,
    message: str = "Explain the issue.",
) -> LLMFinding:
    return LLMFinding(filename, line, severity, confidence, title, message)


def test_deduplication_keeps_the_strongest_normalized_title_match() -> None:
    weaker = _finding(title="Missing validation", confidence=0.65, severity=Severity.LOW)
    stronger = _finding(
        title=" missing   validation ",
        confidence=0.9,
        severity=Severity.HIGH,
        message="Validate the request before use.",
    )

    findings = deduplicate_and_rank_llm_findings((weaker, stronger))

    assert findings == (stronger,)


def test_ranking_orders_by_confidence_then_severity_deterministically() -> None:
    findings = deduplicate_and_rank_llm_findings(
        (
            _finding(title="Low", confidence=0.7, severity=Severity.LOW),
            _finding(title="Medium", confidence=0.8, severity=Severity.MEDIUM),
            _finding(title="High", confidence=0.8, severity=Severity.HIGH),
        )
    )

    assert [finding.title for finding in findings] == ["High", "Medium", "Low"]


def test_ranking_keeps_distinct_findings_on_the_same_line() -> None:
    first = _finding(title="Missing validation", confidence=0.8)
    second = _finding(title="Unsafe shell command", confidence=0.8, severity=Severity.HIGH)

    findings = deduplicate_and_rank_llm_findings((first, second))

    assert set(findings) == {first, second}
