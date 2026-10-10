"""play without a server (E120): the own bot in a thread against a local bot process."""

import pytest

import sbm
from sbm import BLACK, WHITE, InvalidArgumentError, PlayedGame

RESULTS = ("1-0", "0-1", "1/2-1/2")


class First(sbm.Bot):
    def choose_move(self, board, clock):
        return board.legal_moves()[0]


class Broken(sbm.Bot):
    def choose_move(self, board, clock):
        raise RuntimeError("no idea")


def test_play_against_random_alternates_colors():
    played = sbm.play(First, "random", color="white", time="5+0", games=2)

    assert [game.color for game in played] == [WHITE, BLACK]
    assert [game.game_id for game in played] == ["local-1", "local-2"]
    assert all(isinstance(game, PlayedGame) for game in played)
    assert all(game.opponent_name == "random" for game in played)
    assert all(game.result in RESULTS for game in played)


def test_play_against_a_bot_file(tmp_path, capsys):
    path = tmp_path / "other.py"
    path.write_text(
        "import sbm\n"
        "class Other(sbm.Bot):\n"
        "    def choose_move(self, board, clock):\n"
        "        return board.legal_moves()[-1]\n"
        "sbm.run(Other)\n",
        encoding="utf-8",
    )
    [game] = sbm.play(First, str(path), color="black", time="5+0")

    assert (game.color, game.opponent_name) == (BLACK, "other")
    assert "score " in capsys.readouterr().err


def test_an_exception_of_the_bot_ends_the_process(capsys):
    with pytest.raises(SystemExit) as raised:
        sbm.play(Broken, "random", color="white", time="5+0")
    assert raised.value.code == 1
    assert "RuntimeError: no idea" in capsys.readouterr().err


@pytest.mark.parametrize(
    "arguments",
    [
        {"opponent": ""},
        {"opponent": "random", "color": "red"},
        {"opponent": "random", "games": 0},
        {"opponent": "random", "games": True},
        {"opponent": "random", "time": "fast"},
        {"opponent": "random", "discipline": "Blitz"},
        {"opponent": "tcp"},
        {"opponent": "no/such/bot.py"},
    ],
)
def test_invalid_arguments(arguments):
    with pytest.raises(InvalidArgumentError):
        sbm.play(First, **arguments)


@pytest.mark.parametrize(
    ("bot", "arguments"),
    [(First(), {}), (object, {}), (First, {"time": 60})],
)
def test_wrong_types(bot, arguments):
    with pytest.raises(TypeError):
        sbm.play(bot, "random", **arguments)
