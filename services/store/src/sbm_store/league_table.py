"""The table of a tier, computed from its finished matches (E135).

Pure functions: entries are the tier's bots as the season stores them (bot_id, name, version,
lot), games the tier's matches with white, black, status, result, termination and ply_count.
Aborted and unfinished games do not count. Forfeit wins count as wins but not for head to
head, Sonneborn-Berger or the number of moves (E25). After the tiebreaks the lot decides, the
smaller first; withdrawn bots stand at the end without a rank.
"""

from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass, field

from bson import ObjectId

FINISHED = "finished"
FORFEIT = "forfeit_withdrawn"
# The share of the point white and black score per result.
SCORES = {"1-0": (1.0, 0.0), "0-1": (0.0, 1.0), "1/2-1/2": (0.5, 0.5)}
WINS = "wins"
HEAD_TO_HEAD = "head_to_head"
SONNEBORN_BERGER = "sonneborn_berger"
FEWER_MOVES = "fewer_moves"
TIEBREAKS = (WINS, HEAD_TO_HEAD, SONNEBORN_BERGER, FEWER_MOVES)


@dataclass(frozen=True)
class Game:
    """A counted game; score is white's share of the point."""

    white: ObjectId
    black: ObjectId
    score: float
    forfeit: bool
    plies: int


@dataclass
class Row:
    bot: dict
    lot: int
    withdrawn: bool
    games: int = 0
    wins: int = 0
    forfeit_wins: int = 0
    draws: int = 0
    losses: int = 0
    points: float = 0.0
    plies: int = 0
    rank: int | None = None
    outcome: str | None = None
    # The counted games of the bot that were played: opponent and own share of the point.
    played: list[tuple[ObjectId, float]] = field(default_factory=list)

    @property
    def bot_id(self) -> ObjectId:
        return self.bot["bot_id"]

    def to_document(self) -> dict:
        return {
            "bot": self.bot,
            "rank": self.rank,
            "games": self.games,
            "wins": self.wins,
            "forfeit_wins": self.forfeit_wins,
            "draws": self.draws,
            "losses": self.losses,
            "points": self.points,
            "withdrawn": self.withdrawn,
            "outcome": self.outcome,
        }


def counted_games(matches: Iterable[dict]) -> list[Game]:
    """The finished matches with a result, as games; everything else does not count."""
    games = []
    for match in matches:
        score = SCORES.get(match.get("result"))
        if match["status"] != FINISHED or score is None:
            continue
        forfeit = match.get("termination") == FORFEIT
        plies = 0 if forfeit else match.get("ply_count", 0)
        white, black = match["white"]["bot_id"], match["black"]["bot_id"]
        games.append(Game(white, black, score[0], forfeit, plies))
    return games


def table(
    entries: Sequence[dict],
    games: Iterable[Game],
    *,
    points: dict,
    tiebreaks: Sequence[str],
    withdrawn: Iterable[ObjectId] = (),
) -> list[Row]:
    """The rows in their order, ranks set; points holds win, draw and loss."""
    gone = set(withdrawn)
    rows = {
        entry["bot_id"]: Row(
            bot={key: entry[key] for key in ("bot_id", "name", "version")},
            lot=entry["lot"],
            withdrawn=entry["bot_id"] in gone,
        )
        for entry in entries
    }
    counted = [game for game in games if game.white in rows and game.black in rows]
    for game in counted:
        _add(rows[game.white], game.black, game.score, game, points)
        _add(rows[game.black], game.white, 1.0 - game.score, game, points)
    active = [row for row in rows.values() if not row.withdrawn]
    ranked = _order(active, list(tiebreaks), counted, rows, points)
    for rank, row in enumerate(ranked, start=1):
        row.rank = rank
    rest = sorted(
        (row for row in rows.values() if row.withdrawn), key=lambda row: (-row.points, row.lot)
    )
    return ranked + rest


def _add(row: Row, opponent: ObjectId, score: float, game: Game, points: dict) -> None:
    row.games += 1
    row.points += _points_for(score, points)
    if score == 1.0:
        row.wins += 1
        row.forfeit_wins += game.forfeit
    elif score == 0.5:
        row.draws += 1
    else:
        row.losses += 1
    if not game.forfeit:
        row.plies += game.plies
        row.played.append((opponent, score))


def _order(
    group: list[Row], criteria: list[str], games: list[Game], rows: dict, points: dict
) -> list[Row]:
    """Points first, then each tiebreak within the bots still level, the lot last."""
    return _split(
        group, [_by_points, *(_criterion(name) for name in criteria)], games, rows, points
    )


def _split(group: list[Row], keys: list[Callable], games, rows, points) -> list[Row]:
    if len(group) <= 1 or not keys:
        return sorted(group, key=lambda row: row.lot)
    values = keys[0](group, games, rows, points)
    result = []
    for value in sorted(set(values.values()), reverse=True):
        level = [row for row in group if values[row.bot_id] == value]
        result += _split(level, keys[1:], games, rows, points)
    return result


def _criterion(name: str) -> Callable:
    return {
        WINS: _by_wins,
        HEAD_TO_HEAD: _by_head_to_head,
        SONNEBORN_BERGER: _by_sonneborn_berger,
        FEWER_MOVES: _by_fewer_moves,
    }[name]


def _by_points(group, games, rows, points) -> dict:
    return {row.bot_id: row.points for row in group}


def _by_wins(group, games, rows, points) -> dict:
    return {row.bot_id: row.wins for row in group}


def _by_head_to_head(group, games, rows, points) -> dict:
    """Points from the games the bots level with each other played among themselves."""
    level = {row.bot_id for row in group}
    values = dict.fromkeys(level, 0.0)
    for game in games:
        if game.forfeit or game.white not in level or game.black not in level:
            continue
        values[game.white] += _points_for(game.score, points)
        values[game.black] += _points_for(1.0 - game.score, points)
    return values


def _by_sonneborn_berger(group, games, rows, points) -> dict:
    return {
        row.bot_id: sum(score * rows[opponent].points for opponent, score in row.played)
        for row in group
    }


def _by_fewer_moves(group, games, rows, points) -> dict:
    return {row.bot_id: -row.plies for row in group}


def _points_for(score: float, points: dict) -> float:
    if score == 1.0:
        return points["win"]
    if score == 0.5:
        return points["draw"]
    return points["loss"]
