"""What an upload may contain: paths, kinds, sizes and the entry (verifikation.md, E203)."""

import pytest

from sbm.analysis.upload import (
    CSHARP,
    DATA,
    DEFAULT_ENTRY,
    MAX_DATA_BYTES,
    MAX_SOURCE_FILES,
    PYTHON,
    SOURCE,
    UploadError,
    check_upload,
    default_entry,
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


def test_default_entry():
    assert default_entry(PYTHON) == DEFAULT_ENTRY
    assert default_entry(CSHARP) is None


@pytest.mark.parametrize(
    "path, kind",
    [("Bot.cs", SOURCE), ("Engine/Search.cs", SOURCE), ("data/book.txt", DATA)],
)
def test_csharp_file_kind(path, kind):
    assert file_kind(path, CSHARP) == kind


@pytest.mark.parametrize("path", ["bot.py", "MyBot.csproj", "Program.cs.txt", "data/x/y.cs"])
def test_csharp_rejected_paths(path):
    with pytest.raises(UploadError):
        file_kind(path, CSHARP)


def test_python_rejects_cs_files():
    with pytest.raises(UploadError):
        file_kind("Bot.cs")


@pytest.mark.parametrize("entry", ["Bot", "MyBot.TemplateBot", "A.B.C._D9"])
def test_csharp_entry_is_a_class(entry):
    files = check_upload([("Bot.cs", 10), ("data/book.txt", 3)], entry, CSHARP)
    assert [file.kind for file in files] == [SOURCE, DATA]


@pytest.mark.parametrize(
    "files, entry",
    [
        ([("Bot.cs", 1)], "MyBot."),
        ([("Bot.cs", 1)], "9Bot"),
        ([("Bot.cs", 1)], "My Bot"),
        ([("Bot.cs", 1)], "global::MyBot.Bot"),
        ([("Bot.cs", 1)], "MyBot.Bot<int>"),
        ([("Bot.cs", 1)], ".".join(["A"] * 11)),
        ([("data/book.txt", 1)], "MyBot.Bot"),
        ([("Bot.cs", 1), ("bot.cs", 1)], "MyBot.Bot"),
    ],
)
def test_csharp_rejected_uploads(files, entry):
    with pytest.raises(UploadError):
        check_upload(files, entry, CSHARP)
