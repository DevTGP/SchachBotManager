"""The duels of a knockout edition (E176): their games, their decision and the next round.

A duel plays games_per_pairing games, the better seed white in the odd ones. On equal points
follow tiebreak_pairs pairs of games in the tiebreak discipline, then one Armageddon game in it:
colours by lot, a draw is enough for black. A withdrawn bot loses its duel at once. An aborted
game is played again with the same colours, as a new entry for the same phase and game. Once both
duels feeding a place have a winner, the duel of the next round is added; a feeder without one
(both bots withdrew) gives the other side a bye.
"""

import copy
import random
from datetime import datetime

from bson import ObjectId
from pymongo.database import Database

from sbm_store import edition_games, editions, matches
from sbm_store.edition_games import ARMAGEDDON, REGULAR, TIEBREAK
from sbm_store.knockout_bracket import ARMAGEDDON as BY_ARMAGEDDON
from sbm_store.knockout_bracket import (
    GAMES,
    WITHDRAWAL,
    new_duel,
    rounds,
    winner_side,
)
from sbm_store.knockout_bracket import TIEBREAK as BY_TIEBREAK
from sbm_store.league_table import SCORES

OPEN = (matches.QUEUED, matches.RUNNING)


def advance(db: Database, edition: dict, now: datetime, rng: random.Random) -> bool:
    """Moves the duels on as far as their games allow; True once the final is decided."""
    games = {match["_id"]: match for match in edition_games.of_edition(db, edition["_id"])}
    gone = set(edition["withdrawn"])
    duels = copy.deepcopy(edition["duels"])
    changed = False
    for duel in duels:
        if not duel["decided"] and duel["a"] is not None and duel["b"] is not None:
            changed |= _step(duel, games, gone, edition["settings"], rng)
    changed |= _next_round(duels, edition["bracket_size"], gone)
    if changed:
        duels.sort(key=lambda duel: (duel["round"], duel["slot"]))
        saved = editions.save_plan(db, edition, {"duels": duels})
        if saved is not None:
            edition_games.lay_out(db, saved, now)
        return False
    total = rounds(edition["bracket_size"])
    final = next((duel for duel in duels if duel["round"] == total), None)
    return final is not None and final["decided"]


def _step(duel: dict, games: dict, gone: set, settings: dict, rng: random.Random) -> bool:
    """Adds the duel's next games or decides it; False if it waits for games."""
    a, b = duel["a"]["bot_id"], duel["b"]["bot_id"]
    if a in gone or b in gone:
        winner = None if a in gone and b in gone else (b if a in gone else a)
        _decide(duel, winner, WITHDRAWAL)
        return True
    latest = _latest(duel["games"])
    found = {place: games.get(entry["match_id"]) for place, entry in latest.items()}
    if any(match is not None and match["status"] in OPEN for match in found.values()):
        return False
    again = [
        dict(entry, match_id=ObjectId())
        for place, entry in latest.items()
        if found[place] is None or found[place]["status"] == matches.ABORTED
    ]
    if again:
        duel["games"].extend(again)
        return True
    phases = {phase for phase, _ in latest}
    if REGULAR not in phases:
        _add(duel, REGULAR, settings["games_per_pairing"])
        return True
    first, second = _score(latest, found, REGULAR, a)
    if first != second:
        _decide(duel, a if first > second else b, GAMES)
        return True
    if settings["tiebreak_pairs"] > 0:
        if TIEBREAK not in phases:
            _add(duel, TIEBREAK, 2 * settings["tiebreak_pairs"])
            return True
        first, second = _score(latest, found, TIEBREAK, a)
        if first != second:
            _decide(duel, a if first > second else b, BY_TIEBREAK)
            return True
    if ARMAGEDDON not in phases:
        white = rng.choice((a, b))
        black = b if white == a else a
        duel["games"].append(_game(ARMAGEDDON, 1, white, black))
        return True
    entry = latest[(ARMAGEDDON, 1)]
    winner = entry["white"] if found[(ARMAGEDDON, 1)]["result"] == "1-0" else entry["black"]
    _decide(duel, winner, BY_ARMAGEDDON)
    return True


def _decide(duel: dict, winner: ObjectId | None, decided_by: str) -> None:
    duel.update(decided=True, decided_by=decided_by, winner=winner)


def _latest(games: list[dict]) -> dict[tuple[str, int], dict]:
    """The last entry per phase and game; an earlier one was aborted and replaced."""
    return {(entry["phase"], entry["game"]): entry for entry in games}


def _game(phase: str, number: int, white: ObjectId, black: ObjectId) -> dict:
    return {"match_id": ObjectId(), "phase": phase, "game": number, "white": white, "black": black}


def _add(duel: dict, phase: str, count: int) -> None:
    a, b = duel["a"]["bot_id"], duel["b"]["bot_id"]
    for number in range(1, count + 1):
        white, black = (a, b) if number % 2 else (b, a)
        duel["games"].append(_game(phase, number, white, black))


def _score(latest: dict, found: dict, phase: str, a: ObjectId) -> tuple[float, float]:
    """The points of side a and of side b in the finished games of a phase."""
    first = second = 0.0
    for place, entry in latest.items():
        if place[0] != phase:
            continue
        white, black = SCORES.get(found[place]["result"], (0.0, 0.0))
        mine, theirs = (white, black) if entry["white"] == a else (black, white)
        first += mine
        second += theirs
    return first, second


def _next_round(duels: list[dict], bracket_size: int, gone: set) -> bool:
    """Adds each duel whose two feeders are decided; True if it added one."""
    added = False
    grew = True
    while grew:
        grew = False
        places = {(duel["round"], duel["slot"]): duel for duel in duels}
        for round_number in range(1, rounds(bracket_size)):
            for slot in range(1, (bracket_size >> (round_number + 1)) + 1):
                if (round_number + 1, slot) in places:
                    continue
                feeders = (
                    places.get((round_number, 2 * slot - 1)),
                    places.get((round_number, 2 * slot)),
                )
                if all(feeder is not None and feeder["decided"] for feeder in feeders):
                    sides = [_staying(winner_side(feeder), gone) for feeder in feeders]
                    duels.append(new_duel(round_number + 1, slot, *sides))
                    grew = added = True
    return added


def _staying(side: dict | None, gone: set) -> dict | None:
    """A side that withdrew after winning its duel does not move on."""
    return None if side is None or side["bot_id"] in gone else side
