from collections import Counter
from itertools import combinations

import pytest

from sbm_store.league_pairing import cycle, schedule


@pytest.mark.parametrize("count", [2, 3, 4, 5, 6, 9, 10, 32])
def test_each_pair_meets_once_per_cycle(count):
    players = list(range(count))
    rounds = cycle(players)

    pairs = [frozenset(pair) for pairs in rounds for pair in pairs]
    assert Counter(pairs) == Counter(frozenset(pair) for pair in combinations(players, 2))
    assert len(rounds) == count - 1 + count % 2
    for pairs in rounds:
        seated = [player for pair in pairs for player in pair]
        assert len(seated) == len(set(seated))
        assert len(pairs) == count // 2


def test_an_odd_number_gives_each_bot_one_bye():
    rounds = cycle(["a", "b", "c", "d", "e"])

    resting = Counter(
        player
        for pairs in rounds
        for player in "abcde"
        if all(player not in pair for pair in pairs)
    )
    assert resting == Counter("abcde")


def test_colours_stay_balanced_within_one_game():
    whites = Counter(white for pairs in cycle(list(range(10))) for white, _ in pairs)

    assert all(4 <= whites[player] <= 5 for player in range(10))


def test_repetitions_swap_the_colours_and_count_the_rounds_on():
    games = schedule(["a", "b", "c", "d"], 2)

    assert [game.round for game in games] == [1, 1, 2, 2, 3, 3, 4, 4, 5, 5, 6, 6]
    assert [game.board for game in games[:2]] == [0, 1]
    first, second = games[:6], games[6:]
    assert [(game.black, game.white) for game in first] == [
        (game.white, game.black) for game in second
    ]


def test_two_bots_play_as_often_as_set():
    games = schedule(["a", "b"], 3)

    assert [(game.round, game.white, game.black) for game in games] == [
        (1, "a", "b"),
        (2, "b", "a"),
        (3, "a", "b"),
    ]
