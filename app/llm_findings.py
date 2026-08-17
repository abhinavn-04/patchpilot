"""Strict validation for structured findings returned by LLM review adapters."""

import json
from dataclasses import dataclass

from app.findings import Severity
from app.github import ChangedFile


@dataclass(frozen=True)
class LLMFinding:
    """A validated issue reported by an LLM review provider."""

    filename: str
    line: int
    severity: Severity
    confidence: float
    title: str
    message: str


class LLMFindingValidationError(ValueError):
    """Raised when a provider response does not satisfy PatchPilot's finding contract."""


def validate_llm_findings(
    response: str, changed_files: tuple[ChangedFile, ...]
) -> tuple[LLMFinding, ...]:
    """Parse and validate a JSON ``{"findings": [...]}`` provider response."""
    try:
        payload = json.loads(response)
    except json.JSONDecodeError as error:
        raise LLMFindingValidationError("LLM response must be valid JSON.") from error

    if not isinstance(payload, dict) or set(payload) != {"findings"}:
        raise LLMFindingValidationError("LLM response must contain only a findings array.")
    if not isinstance(payload["findings"], list):
        raise LLMFindingValidationError("LLM findings must be an array.")

    allowed_files = {changed_file.filename for changed_file in changed_files}
    return tuple(_validate_finding(item, allowed_files) for item in payload["findings"])


def _validate_finding(item: object, allowed_files: set[str]) -> LLMFinding:
    required_fields = {"filename", "line", "severity", "confidence", "title", "message"}
    if not isinstance(item, dict) or set(item) != required_fields:
        raise LLMFindingValidationError("Each LLM finding must use the required fields only.")

    filename = item["filename"]
    line = item["line"]
    severity = item["severity"]
    confidence = item["confidence"]
    title = item["title"]
    message = item["message"]

    if not isinstance(filename, str) or filename not in allowed_files:
        raise LLMFindingValidationError("LLM finding filename must be a changed file.")
    if not isinstance(line, int) or isinstance(line, bool) or line < 1:
        raise LLMFindingValidationError("LLM finding line must be a positive integer.")
    if not isinstance(severity, str) or severity not in Severity:
        raise LLMFindingValidationError("LLM finding severity must be low, medium, or high.")
    if (
        not isinstance(confidence, (int, float))
        or isinstance(confidence, bool)
        or not 0 <= confidence <= 1
    ):
        raise LLMFindingValidationError("LLM finding confidence must be between 0 and 1.")
    if not isinstance(title, str) or not title.strip():
        raise LLMFindingValidationError("LLM finding title must be non-empty text.")
    if not isinstance(message, str) or not message.strip():
        raise LLMFindingValidationError("LLM finding message must be non-empty text.")

    return LLMFinding(
        filename=filename,
        line=line,
        severity=Severity(severity),
        confidence=float(confidence),
        title=title.strip(),
        message=message.strip(),
    )
