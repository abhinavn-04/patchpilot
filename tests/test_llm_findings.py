import pytest

from app.github import ChangedFile
from app.llm_findings import LLMFindingValidationError, validate_llm_findings


def _changed_files() -> tuple[ChangedFile, ...]:
    return (ChangedFile("app/reviewer.py", "modified", 8, 0, 8, "+review()"),)


def test_validator_returns_typed_structured_findings() -> None:
    findings = validate_llm_findings(
        (
            '{"findings":[{"filename":"app/reviewer.py","line":8,'
            '"severity":"high","confidence":0.9,"title":"Unsafe review path",'
            '"message":"Validate provider output before publishing it."}]}'
        ),
        _changed_files(),
    )

    assert findings[0].severity.value == "high"
    assert findings[0].confidence == 0.9
    assert findings[0].title == "Unsafe review path"


@pytest.mark.parametrize(
    ("response", "message"),
    [
        ("not-json", "valid JSON"),
        ('{"findings": {}}', "must be an array"),
        (
            (
                '{"findings":[{"filename":"README.md","line":1,"severity":"low",'
                '"confidence":0.2,"title":"Title","message":"Message"}]}'
            ),
            "changed file",
        ),
        (
            (
                '{"findings":[{"filename":"app/reviewer.py","line":0,"severity":"low",'
                '"confidence":0.2,"title":"Title","message":"Message"}]}'
            ),
            "positive integer",
        ),
        (
            (
                '{"findings":[{"filename":"app/reviewer.py","line":1,"severity":"urgent",'
                '"confidence":0.2,"title":"Title","message":"Message"}]}'
            ),
            "low, medium, or high",
        ),
        (
            (
                '{"findings":[{"filename":"app/reviewer.py","line":1,"severity":"low",'
                '"confidence":1.1,"title":"Title","message":"Message"}]}'
            ),
            "between 0 and 1",
        ),
    ],
)
def test_validator_rejects_invalid_provider_findings(response: str, message: str) -> None:
    with pytest.raises(LLMFindingValidationError, match=message):
        validate_llm_findings(response, _changed_files())
