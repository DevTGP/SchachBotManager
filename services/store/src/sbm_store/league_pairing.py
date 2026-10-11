"""The round robin of a tier (E134): circle method after Berger, repeated per games_per_pairing.

Pure functions; the bots are opaque values. An odd number of bots gets a bye each round, which
is simply no game.
"""

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Pairing:
    round: int
    board: int
    white: Any
    black: Any


def cycle(players: Sequence) -> list[list[tuple]]:
    """One round robin: per round the (white, black) pairs, board by board.

    The last player stays in place while the others rotate. Board 0, the fixed player's game,
    swaps colours every round; on the other boards the first listed player has white.
    """
    seats = list(players)
    if len(seats) % 2:
        seats.append(None)
    count = len(seats)
    fixed, rotating = seats[-1], seats[:-1]
    rounds = []
    for number in range(count - 1):
        order = rotating[number:] + rotating[:number]
        pairs = [(fixed, order[0]) if number % 2 else (order[0], fixed)]
        pairs += [(order[board], order[count - 1 - board]) for board in range(1, count // 2)]
        rounds.append([pair for pair in pairs if None not in pair])
    return rounds


def schedule(players: Sequence, games_per_pairing: int) -> list[Pairing]:
    """All games of a tier in the order of their rounds; each repetition swaps the colours."""
    base = cycle(players)
    games = []
    for repetition in range(games_per_pairing):
        for number, pairs in enumerate(base):
            for board, (white, black) in enumerate(pairs):
                if repetition % 2:
                    white, black = black, white
                games.append(Pairing(repetition * len(base) + number + 1, board, white, black))
    return games
