from app.filtering import filter_reviewable_files, is_reviewable_file
from app.github import ChangedFile


def changed_file(
    filename: str, *, status: str = "modified", patch: str | None = "@@ -1 +1 @@"
) -> ChangedFile:
    return ChangedFile(
        filename=filename,
        status=status,
        additions=1,
        deletions=0,
        changes=1,
        patch=patch,
    )


def test_filter_keeps_supported_python_source_diffs() -> None:
    reviewable_files = filter_reviewable_files(
        (
            changed_file("app/main.py"),
            changed_file("tests/test_main.py"),
            changed_file("scripts/reindex.py"),
        )
    )

    assert [file.filename for file in reviewable_files] == [
        "app/main.py",
        "tests/test_main.py",
        "scripts/reindex.py",
    ]


def test_filter_skips_generated_binary_and_unsupported_files() -> None:
    candidates = (
        changed_file("package-lock.json"),
        changed_file("web/app.min.js"),
        changed_file("web/app.js.map"),
        changed_file("dist/app.py"),
        changed_file("node_modules/tool/index.py"),
        changed_file("clients/service_pb2.py"),
        changed_file("assets/logo.png"),
        changed_file("README.md"),
        changed_file("app/removed.py", status="removed"),
        changed_file("app/too_large.py", patch=None),
    )

    assert all(not is_reviewable_file(candidate) for candidate in candidates)
    assert filter_reviewable_files(candidates) == ()
