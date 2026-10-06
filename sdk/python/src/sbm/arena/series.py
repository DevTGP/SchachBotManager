"""Several games between two bots with alternating colors, and the score."""

import contextlib
from collections.abc import Callable
from dataclasses import dataclass, replace

from sbm.arena.entrants import Entrant
from sbm.constants import BLACK, WHITE
from sbm.referee import Match, MatchRecord, MatchSettings, MoveRecord


@dataclass
class Score:
    """Games without a result (*) count as unfinished, not as draws."""

    wins: int = 0
    draws: int = 0
    losses: int = 0
    unfinished: int = 0

    @property
    def points(self) -> float:
        return self.wins + self.draws / 2

    @property
    def games(self) -> int:
        return self.wins + self.draws + self.losses + self.unfinished


@dataclass(frozen=True)
class Game:
    """number counts from 1; white and black are the entrants' names."""

    number: int
    white: str
    black: str


class Series:
    """The first entrant has white in odd games, the second in even ones."""

    def __init__(
        self, first: Entrant, second: Entrant, settings: MatchSettings, games: int
    ) -> None:
        if games < 1:
            raise ValueError(f"games={games} must be at least 1")
        self._entrants = (first, second)
        self._settings = settings
        self._games = games
        self.scores = {first.name: Score(), second.name: Score()}

    def play(
        self,
        *,
        on_start: Callable[[Game], None] = lambda game: None,
        on_move: Callable[[MoveRecord], None] | None = None,
        on_end: Callable[[Game, MatchRecord], None] = lambda game, record: None,
    ) -> None:
        for number in range(1, self._games + 1):
            white, black = self._entrants if number % 2 else reversed(self._entrants)
            game = Game(number, white.name, black.name)
            on_start(game)
            record = self._play_one(white, black, number, on_move)
            self._count(game, record)
            on_end(game, record)

    def _play_one(
        self,
        white: Entrant,
        black: Entrant,
        number: int,
        on_move: Callable[[MoveRecord], None] | None,
    ) -> MatchRecord:
        settings = replace(self._settings, game_id=f"{self._settings.game_id}-{number}")
        white_player = white.player()
        try:
            black_player = black.player()
        except BaseException:
            # Interrupted while waiting for a TCP bot: the white player is not in a match yet.
            with contextlib.suppress(Exception):
                white_player.close()
            raise
        return Match(white_player, black_player, settings, on_move=on_move).play()

    def _count(self, game: Game, record: MatchRecord) -> None:
        winner = record.outcome.winner
        for color, name in ((WHITE, game.white), (BLACK, game.black)):
            score = self.scores[name]
            if record.outcome.result == "*":
                score.unfinished += 1
            elif winner is None:
                score.draws += 1
            elif winner == color:
                score.wins += 1
            else:
                score.losses += 1
