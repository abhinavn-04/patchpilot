"""Deterministic selection of pull-request files safe to review."""

from pathlib import PurePosixPath

from app.github import ChangedFile

_GENERATED_FILENAMES = {
    "package-lock.json",
    "poetry.lock",
    "pdm.lock",
    "uv.lock",
    "yarn.lock",
}
_GENERATED_PATH_PARTS = {".git", "__pycache__", "build", "dist", "node_modules", "vendor"}
_GENERATED_SUFFIXES = (".min.js", ".map", ".pyc", "_pb2.py", "_pb2_grpc.py")
_SUPPORTED_SUFFIXES = {".py"}


def is_reviewable_file(changed_file: ChangedFile) -> bool:
    """Return whether a changed file is supported by the current review pipeline."""
    path = PurePosixPath(changed_file.filename)
    filename = path.name.lower()

    if changed_file.status == "removed" or changed_file.patch is None:
        return False
    if filename in _GENERATED_FILENAMES:
        return False
    if any(part in _GENERATED_PATH_PARTS for part in path.parts):
        return False
    if filename.endswith(_GENERATED_SUFFIXES):
        return False
    return path.suffix.lower() in _SUPPORTED_SUFFIXES


def filter_reviewable_files(changed_files: tuple[ChangedFile, ...]) -> tuple[ChangedFile, ...]:
    """Keep only source diffs the current Python review stages understand."""
    return tuple(changed_file for changed_file in changed_files if is_reviewable_file(changed_file))
