"""POST /bots for a C# bot: .cs sources and the bot class instead of an entry file (E202)."""

import pytest
from bson import ObjectId
from sbm_store import bots
from sbm_store.names import BOTS

from bot_uploads import post_upload

SOURCE = b"using Sbm;\n\nnamespace MyBot;\n\npublic sealed class MyBot : Bot { }\n"
FILES = {"MyBot.cs": SOURCE, "Engine/Search.cs": b"namespace MyBot;\n", "data/book.txt": b"e4\n"}


def post_csharp(client, files: dict[str, bytes] = FILES, **fields):
    return post_upload(client, files, **{"language": "csharp", "entry": "MyBot.MyBot", **fields})


def test_the_bot_class_is_the_entry(login, db):
    coder, _ = login()

    response = post_csharp(coder)

    assert response.status_code == 201
    view = response.json
    assert (view["language"], view["details"]["entry"]) == ("csharp", "MyBot.MyBot")
    assert view["details"]["files"] == [
        {"path": "MyBot.cs", "kind": "source", "size": len(SOURCE)},
        {"path": "Engine/Search.cs", "kind": "source", "size": 17},
        {"path": "data/book.txt", "kind": "data", "size": 3},
    ]
    bot = bots.get(db, ObjectId(response.json["id"]))
    assert (bot["language"], bot["entry"], bot.get("program")) == ("csharp", "MyBot.MyBot", None)


def test_a_csharp_bot_must_name_its_class(login):
    coder, _ = login()

    response = post_upload(coder, FILES, language="csharp")

    assert response.status_code == 400
    assert (response.json["code"], response.json["field"]) == ("invalid_parameter", "entry")


@pytest.mark.parametrize(
    ("files", "entry", "path"),
    [
        (FILES, "MyBot.", "MyBot."),
        (FILES, "My Bot", "My Bot"),
        ({**FILES, "bot.py": b""}, "MyBot.MyBot", "bot.py"),
        ({**FILES, "MyBot.csproj": b""}, "MyBot.MyBot", "MyBot.csproj"),
        ({"MyBot.cs": b"", "mybot.cs": b""}, "MyBot.MyBot", "mybot.cs"),
    ],
)
def test_csharp_files_against_the_rules_name_the_culprit(login, db, files, entry, path):
    coder, _ = login()

    response = post_csharp(coder, files, entry=entry)

    assert response.status_code == 400
    assert (response.json["code"], response.json["path"]) == ("invalid_upload", path)
    assert db[BOTS].count_documents({"name": "Sharp"}) == 0


def test_a_csharp_bot_needs_a_source_file(login):
    coder, _ = login()

    response = post_csharp(coder, {"data/book.txt": b"e4\n"})

    assert response.status_code == 400
    assert response.json["code"] == "invalid_upload"
    assert "path" not in response.json
