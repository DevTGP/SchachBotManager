"""The games of an edition's plan (E174–E178): storing those still missing and their jobs.

Each planned game names its match id in the plan (rounds, or the games of the duels), so laying
out a plan again after a crash adds only what is missing and then confirms it with scheduled.
A missing game of a withdrawn or deleted bot stays missing: deleting a bot takes its matches
with it (E105), and they must not come back as waiting games. Participants are bots or accounts
(E182); a game with an account gets no job but waits for readiness (E183). In a round robin only
the games of the current round get jobs, add_jobs gives the next round its jobs (E189).
"""

from collections.abc import Iterator
from datetime import datetime

from bson import ObjectId
from pymongo.database import Database

from sbm_store import competition_pace, editions, jobs, matches, participants, tournaments
from sbm_store.discipline import Discipline
from sbm_store.names import BOTS, MATCHES, USERS

REGULAR = "regular"
TIEBREAK = "tiebreak"
ARMAGEDDON = "armageddon"
PROJECTION = {
    "white.kind": 1,
    "white.bot_id": 1,
    "white.user_id": 1,
    "black.kind": 1,
    "black.bot_id": 1,
    "black.user_id": 1,
    "status": 1,
    "result": 1,
    "termination": 1,
    "ply_count": {"$size": "$moves"},
}


def lay_out(db: Database, edition: dict, now: datetime) -> None:
    """Stores the missing games of the plan and the missing jobs of its waiting games."""
    settings = edition["settings"]
    planned = list(_planned(edition))
    ids = [game["match_id"] for game in planned]
    existing = {match["_id"] for match in db[MATCHES].find({"_id": {"$in": ids}}, {"_id": 1})}
    entries = {participants.key(entry): entry for entry in edition["participants"]}
    staying = _staying(db, edition, entries)
    main = Discipline.from_document(settings["discipline_snapshot"])
    tiebreak = settings.get("tiebreak_discipline_snapshot")
    second = Discipline.from_document(tiebreak) if tiebreak else main
    new = []
    for game in planned:
        if game["match_id"] in existing or not {game["white"], game["black"]} <= staying:
            continue
        context = matches.tournament_context(
            edition,
            round_number=game["round"],
            board=game["board"],
            phase=game.get("phase"),
            game=game.get("game"),
        )
        discipline = main if game.get("phase") in (None, REGULAR) else second
        new.append(
            matches.new_tournament_match(
                _side(entries[game["white"]]),
                _side(entries[game["black"]]),
                discipline,
                context=context,
                priority=settings["priority"],
                now=now,
                match_id=game["match_id"],
            )
        )
    if new:
        db[MATCHES].insert_many(new)
    add_jobs(db, edition, now)
    editions.mark_scheduled(db, edition)


def open_games(db: Database, edition_id: ObjectId) -> bool:
    """Whether a game of the edition waits or runs."""
    query = {"context.edition_id": edition_id, "status": {"$in": [matches.QUEUED, matches.RUNNING]}}
    return db[MATCHES].count_documents(query, limit=1) > 0


def of_edition(db: Database, edition_id: ObjectId) -> list[dict]:
    """The games of an edition with what a table or a duel needs."""
    return list(db[MATCHES].find({"context.edition_id": edition_id}, PROJECTION))


def _planned(edition: dict) -> Iterator[dict]:
    """Each planned game with match_id, white, black, round, board and in a duel phase, game."""
    for planned in edition["rounds"]:
        for pairing in planned["pairings"]:
            yield pairing | {"round": planned["round"]}
    for duel in edition["duels"]:
        for game in duel["games"]:
            yield game | {"round": duel["round"], "board": duel["slot"]}


def _staying(db: Database, edition: dict, entries: dict) -> set:
    """The participants that still exist and have not withdrawn."""
    keys = {"_id": {"$in": list(entries)}}
    present = set(db[BOTS].distinct("_id", keys)) | set(db[USERS].distinct("_id", keys))
    return present - set(edition["withdrawn"])


def _side(entry: dict) -> dict:
    """An edition entry as matches.side takes it; an account keeps its user_id."""
    return {
        "_id": participants.key(entry),
        "user_id": entry.get("user_id"),
        "name": entry["name"],
        "version": entry["version"],
    }


def add_jobs(db: Database, edition: dict, now: datetime) -> int:
    """Jobs for the waiting bot games, in a round robin only those of the current round (E189);
    returns how many were added."""
    group = {"context.edition_id": edition["_id"]}
    competition = jobs.tournament_competition(edition["tournament_id"])
    priority = edition["settings"]["priority"]
    if edition["settings"]["format"] == tournaments.ROUND_ROBIN:
        return competition_pace.add_round_jobs(
            db, group, competition=competition, priority=priority, now=now
        )
    return competition_pace.add_jobs(db, group, competition=competition, priority=priority, now=now)
