"""The games of an edition's plan (E174–E178): storing those still missing and their jobs.

Each planned game names its match id in the plan (rounds, or the games of the duels), so laying
out a plan again after a crash adds only what is missing and then confirms it with scheduled.
A missing game of a withdrawn or deleted bot stays missing: deleting a bot takes its matches
with it (E105), and they must not come back as waiting games.
"""

from collections.abc import Iterator
from datetime import datetime

from bson import ObjectId
from pymongo.database import Database

from sbm_store import editions, jobs, matches
from sbm_store.discipline import Discipline
from sbm_store.names import BOTS, JOBS, MATCHES

REGULAR = "regular"
TIEBREAK = "tiebreak"
ARMAGEDDON = "armageddon"
PROJECTION = {
    "white.bot_id": 1,
    "black.bot_id": 1,
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
    entries = {entry["bot_id"]: entry for entry in edition["participants"]}
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
    _add_jobs(db, edition, now)
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
    present = set(db[BOTS].distinct("_id", {"_id": {"$in": list(entries)}}))
    return present - set(edition["withdrawn"])


def _side(entry: dict) -> dict:
    return {"_id": entry["bot_id"], "name": entry["name"], "version": entry["version"]}


def _add_jobs(db: Database, edition: dict, now: datetime) -> None:
    waiting = [
        match["_id"]
        for match in db[MATCHES]
        .find({"context.edition_id": edition["_id"], "status": matches.QUEUED}, {"_id": 1})
        .sort("_id", 1)
    ]
    if not waiting:
        return
    with_job = set(
        db[JOBS].distinct(
            "payload.match_id", {"type": jobs.MATCH, "payload.match_id": {"$in": waiting}}
        )
    )
    competition = jobs.tournament_competition(edition["tournament_id"])
    priority = edition["settings"]["priority"]
    new = [
        jobs.new_match_job(match_id, priority=priority, now=now, competition=competition)
        for match_id in waiting
        if match_id not in with_job
    ]
    if new:
        db[JOBS].insert_many(new)
