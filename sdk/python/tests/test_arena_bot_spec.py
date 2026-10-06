"""Bots as given on the arena's command line."""

import sys

import pytest

from sbm.arena.bot_spec import BotSpec, BotSpecError, parse_bot, unique_names


def test_tcp():
    assert parse_bot("tcp") == BotSpec("tcp-7470", port=7470)
    assert parse_bot("TCP:7471") == BotSpec("tcp-7471", port=7471)


@pytest.mark.parametrize("text", ["tcp:", "tcp:0", "tcp:65536", "tcp:x", "tcp:-1"])
def test_invalid_port(text):
    with pytest.raises(BotSpecError):
        parse_bot(text)


def test_python_file(tmp_path):
    path = tmp_path / "My Bot.py"
    path.write_text("", encoding="utf-8")
    assert parse_bot(str(path)) == BotSpec("My Bot", [sys.executable, str(path)])


def test_missing_python_file(tmp_path):
    with pytest.raises(BotSpecError, match="not a file"):
        parse_bot(str(tmp_path / "missing.py"))


def test_program_file(tmp_path):
    path = tmp_path / "engine.exe"
    path.write_text("", encoding="utf-8")
    assert parse_bot(str(path)) == BotSpec("engine", [str(path)])


def test_command_named_after_its_file(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "bot.jar").write_text("", encoding="utf-8")
    spec = parse_bot("java -jar bot.jar")
    assert spec.name == "bot"
    expected = "java -jar bot.jar" if sys.platform == "win32" else ["java", "-jar", "bot.jar"]
    assert spec.command == expected


def test_command_named_after_its_program(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert parse_bot("my-engine --depth 3").name == "my-engine"


def test_empty_command():
    with pytest.raises(BotSpecError):
        parse_bot("   ")


def test_long_names_are_cut(tmp_path):
    path = tmp_path / ("b" * 100 + ".py")
    path.write_text("", encoding="utf-8")
    assert parse_bot(str(path)).name == "b" * 64


def test_unique_names():
    same = BotSpec("x" * 64, ["a"])
    first, second = unique_names([same, same])
    assert (first.name, second.name) == ("x" * 62 + "-1", "x" * 62 + "-2")
    assert first.command == ["a"]
    different = [BotSpec("a", ["a"]), BotSpec("b", ["b"])]
    assert unique_names(different) == different


def test_tcp_ports_must_differ():
    with pytest.raises(BotSpecError, match="different ports"):
        unique_names([parse_bot("tcp"), parse_bot("tcp:7470")])
    assert len(unique_names([parse_bot("tcp"), parse_bot("tcp:7471")])) == 2


def test_reference_bots(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "random").write_text("", encoding="utf-8")
    assert parse_bot("Material") == BotSpec("material", [sys.executable, "-m", "sbm.bots.material"])
    assert parse_bot("random").command == [sys.executable, "-m", "sbm.bots.random_mover"]
    assert parse_bot(str(tmp_path / "random")).command == [str(tmp_path / "random")]
