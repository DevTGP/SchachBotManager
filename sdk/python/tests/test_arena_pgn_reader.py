"""Reading games from PGN."""

import pytest

from sbm.arena.pgn_reader import PgnError, read_games

TWO_GAMES = """\
% exported by a test
[Event "Test \\"A\\""]
[White "a"]

1. e4 {best by test} e5 2.Nf3 $1 (2. f4 exf4 (2... d5)) Nc6; a comment
3. Bb5 a6 1-0

[Event "B"]
[SetUp "1"]
[FEN "4k3/8/8/8/8/8/4P3/4K3 b - - 0 40"]

40... Kd8 41. e4 Ke8 *
"""


def test_two_games():
    first, second = read_games(TWO_GAMES)
    assert first.tags == {"Event": 'Test "A"', "White": "a"}
    assert first.moves == ["e4", "e5", "Nf3", "Nc6", "Bb5", "a6"]
    assert second.tags["FEN"] == "4k3/8/8/8/8/8/4P3/4K3 b - - 0 40"
    assert second.moves == ["Kd8", "e4", "Ke8"]


def test_game_without_result():
    first, second = read_games('[Event "x"]\n1. d4 d5\n[Event "y"]\n1. c4')
    assert (first.moves, second.moves) == (["d4", "d5"], ["c4"])


def test_empty_text():
    assert read_games("\n\n") == []


@pytest.mark.parametrize("text", ["1. e4 (e5", "1. e4 ) e5", "1. e4 {open", "[Event x]"])
def test_invalid(text):
    with pytest.raises(PgnError):
        read_games(text)
