from app.findings import Severity, normalize_static_signals
from app.static_analysis import StaticSignal


def test_normalization_assigns_severity_by_rule() -> None:
    signals = (
        StaticSignal("app/worker.py", 10, "python.unsafe-eval", "security", "Avoid eval."),
        StaticSignal("app/worker.py", 11, "python.bare-except", "reliability", "Be specific."),
    )

    findings = normalize_static_signals(signals)

    assert [(finding.rule_id, finding.severity) for finding in findings] == [
        ("python.unsafe-eval", Severity.HIGH),
        ("python.bare-except", Severity.MEDIUM),
    ]
    assert findings[0].filename == "app/worker.py"
    assert findings[0].line == 10


def test_normalization_marks_unknown_rules_low_severity() -> None:
    findings = normalize_static_signals(
        (StaticSignal("app/worker.py", 8, "python.future-rule", "style", "Future check."),)
    )

    assert findings[0].severity is Severity.LOW
