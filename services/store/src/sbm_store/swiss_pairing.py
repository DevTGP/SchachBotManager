"""The pairing of one round of the Swiss system (E175).

Pure functions on Player values in standing order (points, then seed). The bye goes to the
lowest bot without one; a depth-first search then pairs the rest without repeats, preferring
opponents with the same points and, within a score group, the top half against the bottom half.
If no such pairing exists it allows one repeat, then two and so on; a search that runs out of
budget falls back to pairing in order.
"""

from collections.abc import Hashable, Sequence
from dataclasses import dataclass

WHITE = "white"
BLACK = "black"
# Nodes the search may visit per number of allowed repeats; far more than small fields need.
BUDGET = 20_000


@dataclass(frozen=True)
class Player:
    bot_id: Hashable
    points: float
    whites: int = 0
    blacks: int = 0
    last_color: str | None = None
    had_bye: bool = False


@dataclass(frozen=True)
class Round:
    bye: Hashable | None
    # (white, black) per board, board 1 first.
    pairs: list[tuple[Hashable, Hashable]]


def pair(players: Sequence[Player], played: set[frozenset], *, first_round: bool = False) -> Round:
    """The next round; played holds the pairs of bots that met already."""
    order = list(players)
    bye = None
    if len(order) % 2:
        free = [player for player in order if not player.had_bye]
        bye = (free or order)[-1].bot_id
        order = [player for player in order if player.bot_id != bye]
    rank = {player.bot_id: index for index, player in enumerate(order)}
    pairs = _search(order, played) or _in_order(order)
    pairs.sort(key=lambda pair: min(rank[pair[0].bot_id], rank[pair[1].bot_id]))
    boards = []
    for board, (first, second) in enumerate(pairs, start=1):
        better, worse = (
            (first, second) if rank[first.bot_id] < rank[second.bot_id] else (second, first)
        )
        if first_round:
            white, black = (better, worse) if board % 2 else (worse, better)
        else:
            white, black = _colors(better, worse)
        boards.append((white.bot_id, black.bot_id))
    return Round(bye, boards)


def _colors(better: Player, worse: Player) -> tuple[Player, Player]:
    """White for the one with fewer whites, then for the one who had black last, then the
    better placed one."""
    if better.whites != worse.whites:
        return (better, worse) if better.whites < worse.whites else (worse, better)
    if (better.last_color == BLACK) != (worse.last_color == BLACK):
        return (better, worse) if better.last_color == BLACK else (worse, better)
    return better, worse


def _search(order: list[Player], played: set[frozenset]) -> list[tuple[Player, Player]] | None:
    preferences = _preferences(order)
    for repeats in range(len(order) // 2 + 1):
        budget = [BUDGET]
        found = _extend(list(order), [], repeats, played, preferences, budget)
        if found is not None:
            return found
        if budget[0] <= 0:
            return None
    return None


def _extend(
    rest: list[Player],
    pairs: list[tuple[Player, Player]],
    repeats: int,
    played: set[frozenset],
    preferences: dict,
    budget: list[int],
) -> list[tuple[Player, Player]] | None:
    if not rest:
        return list(pairs)
    budget[0] -= 1
    if budget[0] <= 0:
        return None
    first = rest[0]
    for candidate in preferences[first.bot_id]:
        if candidate not in rest[1:]:
            continue
        repeat = frozenset((first.bot_id, candidate.bot_id)) in played
        if repeat and repeats == 0:
            continue
        pairs.append((first, candidate))
        left = [player for player in rest[1:] if player is not candidate]
        found = _extend(left, pairs, repeats - repeat, played, preferences, budget)
        if found is not None:
            return found
        pairs.pop()
        if budget[0] <= 0:
            return None
    return None


def _preferences(order: list[Player]) -> dict:
    """Per bot the others in the order to try: the ideal opponent of its score group first
    (top half against bottom half), then by distance in points, then by standing."""
    groups: dict[float, list[Player]] = {}
    for player in order:
        groups.setdefault(player.points, []).append(player)
    result = {}
    for player in order:
        group = groups[player.points]
        position = group.index(player)
        half = len(group) // 2
        ideal = position + half if position < half else position - half

        def key(other: Player, *, player=player, group=group, ideal=ideal) -> tuple:
            if other.points == player.points:
                return (0.0, abs(group.index(other) - ideal), 0)
            return (abs(other.points - player.points), 0, order.index(other))

        result[player.bot_id] = sorted((other for other in order if other is not player), key=key)
    return result


def _in_order(order: list[Player]) -> list[tuple[Player, Player]]:
    return [(order[index], order[index + 1]) for index in range(0, len(order) - 1, 2)]
