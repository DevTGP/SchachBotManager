"""What an upload may contain: paths, kinds, sizes and the entry file (verifikation.md)."""

import pytest

from sbm.analysis.upload import (
    DATA,
    MAX_DATA_BYTES,
    MAX_SOURCE_FILES,
    SOURCE,
    UploadError,
    check_upload,
    file_kind,
)


@pytest.mark.parametrize(
    "path, kind",
    [
        ("bot.py", SOURCE),
        ("engine/search.py", SOURCE),
        ("engine/__init__.py", SOURCE),
        ("data/book.txt", DATA),
        ("data/weights.bin", DATA),
        ("data/no-suffix", DATA),
    ],
)
def test_file_kind(path, kind):
    assert file_kind(path) == kind


@pytest.mark.parametrize(
    "path",
    [
        "README.md",
        "engine/notes.txt",
        "data/sub/book.txt",
        "data",
        "../bot.py",
        "./bot.py",
        "/bot.py",
        "engine//bot.py",
        ".hidden.py",
        "-x.py",
        "engine\\bot.py",
        "bö.py",
        "a b.py",
        "a/" * 8 + "bot.py",
        "x" * 198 + ".py",
    ],
)
def test_rejected_paths(path):
    with pytest.raises(UploadError) as error:
        file_kind(path)
    assert error.value.path == path


def test_check_upload_returns_kinds():
    files = check_upload([("bot.py", 10), ("lib/x.py", 5), ("data/book.txt", 3)], "bot.py")
    assert [(file.path, file.kind, file.size) for file in files] == [
        ("bot.py", SOURCE, 10),
        ("lib/x.py", SOURCE, 5),
        ("data/book.txt", DATA, 3),
    ]


@pytest.mark.parametrize(
    "files, entry",
    [
        ([("bot.py", 1), ("Bot.py", 1)], "bot.py"),
        ([("bot.py", 1), ("lib.py", 1), ("lib.py/x.py", 1)], "bot.py"),
        ([("bot.py", 1), ("Lib.py/x.py", 1), ("lib.py", 1)], "bot.py"),
        ([("main.py", 1)], "bot.py"),
        ([("lib/bot.py", 1)], "lib/bot.py"),
        ([("bot.py", 1), ("data/bot.txt", 1)], "data/bot.txt"),
        ([("bot.py", 1)] + [(f"m{i}.py", 1) for i in range(MAX_SOURCE_FILES)], "bot.py"),
        ([("bot.py", 1), ("data/a", MAX_DATA_BYTES), ("data/b", 1)], "bot.py"),
        ([("bot.py", 1024 * 1024 + 1)], "bot.py"),
        ([], "bot.py"),
    ],
)
def test_rejected_uploads(files, entry):
    with pytest.raises(UploadError):
        check_upload(files, entry)


def test_limits_are_inclusive():
    files = [("bot.py", 1), ("data/a", MAX_DATA_BYTES)]
    files += [(f"m{i}.py", 1) for i in range(MAX_SOURCE_FILES - 1)]
    assert len(check_upload(files, "bot.py")) == MAX_SOURCE_FILES + 1
