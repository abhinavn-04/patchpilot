from app.github import ChangedFile
from app.static_analysis import analyze_python_diff


def _changed_python_file(patch: str) -> ChangedFile:
    return ChangedFile(
        filename="app/worker.py",
        status="modified",
        additions=4,
        deletions=0,
        changes=4,
        patch=patch,
    )


def test_analysis_reports_risky_added_lines_with_pull_request_line_numbers() -> None:
    changed_file = _changed_python_file(
        """@@ -10,2 +10,5 @@
 context_line()
+value = eval(user_input)
+subprocess.run(command, shell=True)
+token = "hard-coded"
+except:
"""
    )

    signals = analyze_python_diff(changed_file)

    assert [(signal.rule_id, signal.line) for signal in signals] == [
        ("python.unsafe-eval", 11),
        ("python.shell-true", 12),
        ("python.hardcoded-credential", 13),
        ("python.bare-except", 14),
    ]


def test_analysis_ignores_removed_and_context_lines() -> None:
    changed_file = _changed_python_file(
        """@@ -1,2 +1,2 @@
-value = eval(user_input)
 value = safe_parse(user_input)
+result = transform(value)
"""
    )

    assert analyze_python_diff(changed_file) == ()
