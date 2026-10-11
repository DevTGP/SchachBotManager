"""The table of a tier or tournament edition, computed from its finished matches (E135, E177).

Pure functions: entries are the participants as the season or edition stores them (bot_id
or user_id, name, version, lot), games their matches with white, black, status, result,
termination and ply_count. Rows are keyed by participants.key (E182). Aborted and unfinished
games do not count. Forfeit wins, from a withdrawal or an absence, count as wins but not for
head to head, Sonneborn-Berger, Buchholz or the number of moves (E25, E184); "0-0" after both
sides stayed away is a loss for both. A bye of the Swiss system counts as a win's points
without a game. After the tiebreaks the lot decides, the smaller first; withdrawn
participants stand at the end without a rank.
"""

from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass, field

from bson import ObjectId

from sbm_store import participants

FINISHED = "finished"
FORFEIT = "forfeit_withdrawn"
# A competition game an account did not turn up for by its deadline (E184).
FORFEIT_ABSENT = "forfeit_absent"
FORFEITS = (FORFEIT, FORFEIT_ABSENT)
# The share of the point white and black score per result; "0-0" when both stayed away.
SCORES = {"1-0": (1.0, 0.0), "0-1": (0.0, 1.0), "1/2-1/2": (0.5, 0.5), "0-0": (0.0, 0.0)}
WINS = "wins"
HEAD_TO_HEAD = "head_to_head"
SONNEBORN_BERGER = "sonneborn_berger"
FEWER_MOVES = "fewer_moves"
BUCHHOLZ = "buchholz"
TIEBREAKS = (WINS, HEAD_TO_HEAD, SONNEBORN_BERGER, FEWER_MOVES)
# Tournaments may also break ties by Buchholz (E177).
EDITION_TIEBREAKS = (*TIEBREAKS, BUCHHOLZ)


@dataclass(frozen=True)
class Game:
    """A counted game between two participant keys and the share of the point of each."""

    white: ObjectId
    black: ObjectId
    white_score: float
    black_score: float
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
    byes: int = 0
    points: float = 0.0
    buchholz: float = 0.0
    plies: int = 0
    rank: int | None = None
    outcome: str | None = None
    # The counted games of the participant that were played: opponent and own share.
    played: list[tuple[ObjectId, float]] = field(default_factory=list)

    @property
    def key(self) -> ObjectId:
        return participants.key(self.bot)

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

    def to_edition_document(self) -> dict:
        """The row of a tournament table: without outcome, with byes and Buchholz."""
        document = self.to_document()
        del document["outcome"]
        return document | {"byes": self.byes, "buchholz": self.buchholz}


def counted_games(matches: Iterable[dict]) -> list[Game]:
    """The finished matches with a result, as games; everything else does not count."""
    games = []
    for match in matches:
        score = SCORES.get(match.get("result"))
        if match["status"] != FINISHED or score is None:
            continue
        forfeit = match.get("termination") in FORFEITS
        plies = 0 if forfeit else match.get("ply_count", 0)
        white, black = participants.key(match["white"]), participants.key(match["black"])
        games.append(Game(white, black, score[0], score[1], forfeit, plies))
    return games


def table(
    entries: Sequence[dict],
    games: Iterable[Game],
    *,
    points: dict,
    tiebreaks: Sequence[str],
    withdrawn: Iterable[ObjectId] = (),
    byes: Mapping[ObjectId, int] | None = None,
) -> list[Row]:
    """The rows in their order, ranks set; points holds win, draw and loss, byes the number of
    byes per participant key."""
    gone = set(withdrawn)
    rows = {
        participants.key(entry): Row(
            bot=row_participant(entry),
            lot=entry["lot"],
            withdrawn=participants.key(entry) in gone,
        )
        for entry in entries
    }
    counted = [game for game in games if game.white in rows and game.black in rows]
    for game in counted:
        _add(rows[game.white], game.black, game.white_score, game, points)
        _add(rows[game.black], game.white, game.black_score, game, points)
    for key, count in (byes or {}).items():
        if key in rows:
            rows[key].byes += count
            rows[key].points += count * points["win"]
    for row in rows.values():
        row.buchholz = sum(rows[opponent].points for opponent, _ in row.played)
    active = [row for row in rows.values() if not row.withdrawn]
    ranked = _order(active, list(tiebreaks), counted, rows, points)
    for rank, row in enumerate(ranked, start=1):
        row.rank = rank
    rest = sorted(
        (row for row in rows.values() if row.withdrawn), key=lambda row: (-row.points, row.lot)
    )
    return ranked + rest


def row_participant(entry: dict) -> dict:
    """The participant as a row names it: bot_id or user_id, name and version."""
    return {
        "bot_id": entry.get("bot_id"),
        "user_id": entry.get("user_id"),
        "name": entry["name"],
        "version": entry.get("version"),
    }


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
        level = [row for row in group if values[row.key] == value]
        result += _split(level, keys[1:], games, rows, points)
    return result


def _criterion(name: str) -> Callable:
    return {
        WINS: _by_wins,
        HEAD_TO_HEAD: _by_head_to_head,
        SONNEBORN_BERGER: _by_sonneborn_berger,
        FEWER_MOVES: _by_fewer_moves,
        BUCHHOLZ: _by_buchholz,
    }[name]


def _by_points(group, games, rows, points) -> dict:
    return {row.key: row.points for row in group}


def _by_wins(group, games, rows, points) -> dict:
    return {row.key: row.wins for row in group}


def _by_head_to_head(group, games, rows, points) -> dict:
    """Points from the games the participants level with each other played among themselves."""
    level = {row.key for row in group}
    values = dict.fromkeys(level, 0.0)
    for game in games:
        if game.forfeit or game.white not in level or game.black not in level:
            continue
        values[game.white] += _points_for(game.white_score, points)
        values[game.black] += _points_for(game.black_score, points)
    return values


def _by_sonneborn_berger(group, games, rows, points) -> dict:
    return {
        row.key: sum(score * rows[opponent].points for opponent, score in row.played)
        for row in group
    }


def _by_buchholz(group, games, rows, points) -> dict:
    return {row.key: row.buchholz for row in group}


def _by_fewer_moves(group, games, rows, points) -> dict:
    return {row.key: -row.plies for row in group}


def _points_for(score: float, points: dict) -> float:
    if score == 1.0:
        return points["win"]
    if score == 0.5:
        return points["draw"]
    return points["loss"]
