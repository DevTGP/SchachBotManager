"""Series of games between two entrants with alternating colors."""

import time

import pytest
from scripted_player import ScriptedPlayer, move, ready, resign

from sbm.arena.entrants import Entrant
from sbm.arena.series import Score, Series
from sbm.referee import MatchSettings


class RealTime:
    """The scripted players' time source on the referee's real clock; answers take no time."""

    @property
    def ns(self) -> int:
        return time.monotonic_ns()

    @ns.setter
    def ns(self, value: int) -> None:
        pass


class ScriptedEntrant(Entrant):
    def __init__(self, name: str, script: list) -> None:
        super().__init__(name)
        self.script = script
        self.players: list[ScriptedPlayer] = []

    def player(self) -> ScriptedPlayer:
        player = ScriptedPlayer(self.name, RealTime(), self.script)
        self.players.append(player)
        return player


SETTINGS = MatchSettings(initial_time_ms=10_000, game_id="series")


def test_colors_alternate_and_scores_add_up():
    # The opener plays e4 with white; the quitter resigns at its first turn.
    opener = ScriptedEntrant("opener", [ready(), move("e2e4")])
    quitter = ScriptedEntrant("quitter", [ready(), resign()])
    series = Series(opener, quitter, SETTINGS, 3)
    started, ended = [], []
    series.play(
        on_start=started.append, on_end=lambda game, record: ended.append(record.outcome.result)
    )
    assert [(game.number, game.white, game.black) for game in started] == [
        (1, "opener", "quitter"),
        (2, "quitter", "opener"),
        (3, "opener", "quitter"),
    ]
    assert ended == ["1-0", "0-1", "1-0"]
    assert series.scores == {
        "opener": Score(wins=3),
        "quitter": Score(losses=3),
    }
    assert len(opener.players) == 3
    init = opener.players[1].sent[0]
    assert (init["type"], init["game_id"], init["color"]) == ("init", "series-2", "black")
    assert all(player.events[-1] == ("close",) for player in opener.players + quitter.players)


def test_score():
    score = Score(wins=1, draws=3, losses=2, unfinished=1)
    assert (score.points, score.games) == (2.5, 7)


def test_white_closed_when_black_never_comes():
    white = ScriptedEntrant("white", [ready()])

    class Interrupted(Entrant):
        def player(self):
            raise KeyboardInterrupt

    with pytest.raises(KeyboardInterrupt):
        Series(white, Interrupted("black"), SETTINGS, 1).play()
    assert white.players[0].events == [("close",)]


def test_at_least_one_game():
    with pytest.raises(ValueError):
        Series(ScriptedEntrant("a", []), ScriptedEntrant("b", []), SETTINGS, 0)
