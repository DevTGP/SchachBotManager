"""What an upload of a Python bot may contain (verifikation.md); the web API, the runner and
sbm-check apply the same rules.

Paths are relative and use /. Source files are .py files outside data/; data files lie directly
in data/, since load_data only takes plain names (E62).
"""

import re
from collections.abc import Iterable
from dataclasses import dataclass

SOURCE = "source"
DATA = "data"
DATA_DIR = "data"
MAX_SOURCE_FILES = 100
MAX_SOURCE_BYTES = 1024 * 1024
MAX_DATA_FILES = 100
# E30: data files up to 1 MB in all.
MAX_DATA_BYTES = 1024 * 1024
MAX_DEPTH = 8
MAX_PATH_LENGTH = 200
DEFAULT_ENTRY = "bot.py"
_COMPONENT = re.compile(r"[A-Za-z0-9_][A-Za-z0-9_.-]*")


class UploadError(ValueError):
    """The upload breaks a rule; path names the file, if one is to blame."""

    def __init__(self, message: str, path: str | None = None) -> None:
        super().__init__(message)
        self.path = path


@dataclass(frozen=True)
class UploadFile:
    path: str
    kind: str
    size: int


def file_kind(path: str) -> str:
    """SOURCE or DATA; raises UploadError for a path an upload may not contain."""
    if len(path) > MAX_PATH_LENGTH:
        raise UploadError(f"the path is longer than {MAX_PATH_LENGTH} characters", path)
    parts = path.split("/")
    if len(parts) > MAX_DEPTH:
        raise UploadError(f"the path is deeper than {MAX_DEPTH} levels", path)
    for part in parts:
        if not _COMPONENT.fullmatch(part):
            raise UploadError(
                "every part of a path must start with a letter, digit or _ and contain only "
                "letters, digits, _, . and -",
                path,
            )
    if parts[0] == DATA_DIR:
        if len(parts) != 2:
            raise UploadError(f"data files must lie directly in {DATA_DIR}/", path)
        return DATA
    if not path.endswith(".py"):
        raise UploadError(f"only .py files and data files in {DATA_DIR}/ are allowed", path)
    return SOURCE


def check_upload(files: Iterable[tuple[str, int]], entry: str) -> list[UploadFile]:
    """Checks paths, sizes and the entry file; files are (path, size in bytes)."""
    checked = [UploadFile(path, file_kind(path), size) for path, size in files]
    _check_unique(checked)
    for kind, max_files, max_bytes in (
        (SOURCE, MAX_SOURCE_FILES, MAX_SOURCE_BYTES),
        (DATA, MAX_DATA_FILES, MAX_DATA_BYTES),
    ):
        of_kind = [file for file in checked if file.kind == kind]
        if len(of_kind) > max_files:
            raise UploadError(f"more than {max_files} {kind} files")
        if sum(file.size for file in of_kind) > max_bytes:
            raise UploadError(f"the {kind} files are larger than {max_bytes} bytes in all")
    if "/" in entry or not entry.endswith(".py"):
        raise UploadError("the entry file must be a .py file in the top folder", entry)
    if not any(file.path == entry and file.kind == SOURCE for file in checked):
        raise UploadError("the entry file is missing", entry)
    return checked


def _check_unique(files: list[UploadFile]) -> None:
    """Also across case, since a bot written on Windows or macOS must not depend on it."""
    paths: set[str] = set()
    folders: set[str] = set()
    for file in files:
        key = file.path.lower()
        if key in paths or key in folders:
            raise UploadError("the path occurs twice", file.path)
        paths.add(key)
        parts = key.split("/")
        folders.update("/".join(parts[:end]) for end in range(1, len(parts)))
    if not paths.isdisjoint(folders):
        clash = min(paths & folders)
        raise UploadError("a file has the same name as a folder", clash)
