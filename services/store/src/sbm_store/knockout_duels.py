"""The duels of a knockout edition (E176): their games, their decision and the next round.

A duel plays games_per_pairing games, the better seed white in the odd ones. On equal points
follow tiebreak_pairs pairs of games in the tiebreak discipline, then one Armageddon game in it:
colours by lot, a draw is enough for black. A withdrawn participant loses its duel at once, an
account absent at the deadline of a game too; the duel's other waiting games are then aborted
(E184). An aborted game of an undecided duel is played again with the same colours, as a new
entry for the same phase and game. Once both duels feeding a place have a winner, the duel of
the next round is added; a feeder without one (both sides withdrew or were absent) gives the
other side a bye. Sides are participant keys (E182).
"""

import copy
import random
from datetime import datetime

from bson import ObjectId
from pymongo.database import Database

from sbm_store import edition_games, editions, jobs, matches
from sbm_store import participants as participant_keys
from sbm_store.edition_games import ARMAGEDDON, REGULAR, TIEBREAK
from sbm_store.knockout_bracket import (
    ABSENCE,
    GAMES,
    WITHDRAWAL,
    new_duel,
    rounds,
    winner_side,
)
from sbm_store.knockout_bracket import ARMAGEDDON as BY_ARMAGEDDON
from sbm_store.knockout_bracket import TIEBREAK as BY_TIEBREAK
from sbm_store.league_table import SCORES

OPEN = (matches.QUEUED, matches.RUNNING)
DECIDED = "the duel was decided by absence"


def advance(db: Database, edition: dict, now: datetime, rng: random.Random) -> bool:
    """Moves the duels on as far as their games allow; True once the final is decided."""
    games = {match["_id"]: match for match in edition_games.of_edition(db, edition["_id"])}
    gone = set(edition["withdrawn"])
    duels = copy.deepcopy(edition["duels"])
    changed = False
    decided = []
    for duel in duels:
        if not duel["decided"] and duel["a"] is not None and duel["b"] is not None:
            changed |= _step(duel, games, gone, edition["settings"], rng)
            if duel["decided"]:
                decided.append(duel)
    changed |= _next_round(duels, edition["bracket_size"], gone)
    if changed:
        duels.sort(key=lambda duel: (duel["round"], duel["slot"]))
        saved = editions.save_plan(db, edition, {"duels": duels})
        if saved is not None:
            _drop_waiting(db, decided, games, now)
            edition_games.lay_out(db, saved, now)
        return False
    total = rounds(edition["bracket_size"])
    final = next((duel for duel in duels if duel["round"] == total), None)
    return final is not None and final["decided"]


def _step(duel: dict, games: dict, gone: set, settings: dict, rng: random.Random) -> bool:
    """Adds the duel's next games or decides it; False if it waits for games."""
    a, b = participant_keys.key(duel["a"]), participant_keys.key(duel["b"])
    if a in gone or b in gone:
        winner = None if a in gone and b in gone else (b if a in gone else a)
        _decide(duel, winner, WITHDRAWAL)
        return True
    latest = _latest(duel["games"])
    found = {place: games.get(entry["match_id"]) for place, entry in latest.items()}
    absent = _absence(latest, found)
    if absent is not False:
        _decide(duel, absent, ABSENCE)
        return True
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


def _drop_waiting(db: Database, decided: list[dict], games: dict, now: datetime) -> None:
    """Aborts the waiting games of duels decided before they were played out, which an absence
    does (E184); a game already running ends as it is and counts for nothing."""
    for duel in decided:
        for entry in duel["games"]:
            match = games.get(entry["match_id"])
            if match is not None and match["status"] == matches.QUEUED:
                jobs.cancel_match(db, match["_id"], now, running=False)
                matches.abort(db, match["_id"], DECIDED, now)


def _absence(latest: dict, found: dict) -> ObjectId | None | bool:
    """The winner of a game lost by absence (None if both were absent); False without one."""
    for place, entry in latest.items():
        match = found[place]
        if match is not None and match.get("termination") == matches.FORFEIT_ABSENT:
            result = match["result"]
            return (
                entry["white"] if result == "1-0" else entry["black"] if result == "0-1" else None
            )
    return False


def _latest(games: list[dict]) -> dict[tuple[str, int], dict]:
    """The last entry per phase and game; an earlier one was aborted and replaced."""
    return {(entry["phase"], entry["game"]): entry for entry in games}


def _game(phase: str, number: int, white: ObjectId, black: ObjectId) -> dict:
    return {"match_id": ObjectId(), "phase": phase, "game": number, "white": white, "black": black}


def _add(duel: dict, phase: str, count: int) -> None:
    a, b = participant_keys.key(duel["a"]), participant_keys.key(duel["b"])
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
    return None if side is None or participant_keys.key(side) in gone else side
