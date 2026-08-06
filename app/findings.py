"""Normalized findings ready for later ranking and feedback publishing."""

from dataclasses import dataclass
from enum import StrEnum

from app.static_analysis import StaticSignal


class Severity(StrEnum):
    """Ordered impact levels used by PatchPilot's review pipeline."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass(frozen=True)
class ReviewFinding:
    """A static signal enriched with a stable severity level."""

    filename: str
    line: int
    rule_id: str
    category: str
    severity: Severity
    message: str


_SEVERITY_BY_RULE = {
    "python.unsafe-eval": Severity.HIGH,
    "python.shell-true": Severity.HIGH,
    "python.hardcoded-credential": Severity.HIGH,
    "python.bare-except": Severity.MEDIUM,
}


def normalize_static_signals(signals: tuple[StaticSignal, ...]) -> tuple[ReviewFinding, ...]:
    """Convert raw static-analysis signals to findings with deterministic severity."""
    return tuple(
        ReviewFinding(
            filename=signal.filename,
            line=signal.line,
            rule_id=signal.rule_id,
            category=signal.category,
            severity=_SEVERITY_BY_RULE.get(signal.rule_id, Severity.LOW),
            message=signal.message,
        )
        for signal in signals
    )
