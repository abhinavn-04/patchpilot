"""Deterministic checks for newly added Python pull-request lines."""

from dataclasses import dataclass
import re

from app.github import ChangedFile

_HUNK_HEADER = re.compile(r"^@@ -\d+(?:,\d+)? \+(?P<start>\d+)(?:,\d+)? @@")
_UNSAFE_EVAL = re.compile(r"\b(?:eval|exec)\s*\(")
_SHELL_TRUE = re.compile(
    r"\bsubprocess\.(?:run|call|Popen|check_output)\s*\(.*\bshell\s*=\s*True\b"
)
_HARDCODED_CREDENTIAL = re.compile(
    r"\b(?:api[_-]?key|password|secret|token)\s*=\s*['\"][^'\"]+['\"]",
    re.IGNORECASE,
)
_BARE_EXCEPT = re.compile(r"^\s*except\s*:\s*$")


@dataclass(frozen=True)
class StaticSignal:
    """A raw deterministic signal found in an added pull-request line."""

    filename: str
    line: int
    rule_id: str
    category: str
    message: str


def analyze_python_diff(changed_file: ChangedFile) -> tuple[StaticSignal, ...]:
    """Inspect added Python lines and return raw review signals with PR line numbers."""
    if not changed_file.filename.endswith(".py") or changed_file.patch is None:
        return ()

    signals: list[StaticSignal] = []
    new_line_number: int | None = None

    for patch_line in changed_file.patch.splitlines():
        hunk_match = _HUNK_HEADER.match(patch_line)
        if hunk_match:
            new_line_number = int(hunk_match.group("start"))
            continue
        if new_line_number is None:
            continue
        if patch_line.startswith("+") and not patch_line.startswith("+++"):
            source_line = patch_line[1:]
            signals.extend(_signals_for_line(changed_file.filename, new_line_number, source_line))
            new_line_number += 1
        elif patch_line.startswith(" "):
            new_line_number += 1

    return tuple(signals)


def _signals_for_line(filename: str, line: int, source_line: str) -> tuple[StaticSignal, ...]:
    checks = (
        (
            _UNSAFE_EVAL,
            "python.unsafe-eval",
            "security",
            "Avoid eval or exec; use explicit parsing or dispatch instead.",
        ),
        (
            _SHELL_TRUE,
            "python.shell-true",
            "security",
            "Avoid shell=True and pass a command argument list to subprocess.",
        ),
        (
            _HARDCODED_CREDENTIAL,
            "python.hardcoded-credential",
            "security",
            "Read credentials from an environment variable or secret manager.",
        ),
        (
            _BARE_EXCEPT,
            "python.bare-except",
            "reliability",
            "Catch a specific exception type to avoid masking failures.",
        ),
    )
    return tuple(
        StaticSignal(filename, line, rule_id, category, message)
        for pattern, rule_id, category, message in checks
        if pattern.search(source_line)
    )
