"""The rounds of a Swiss edition (E175): the next one is paired once the current one has ended.

Standing for the pairing is points (games plus byes), then seed. Withdrawn participants are no
longer paired. The edition is done after min(rounds, participants − 1) rounds or when fewer
than two participants are left.
"""

from datetime import datetime

from bson import ObjectId
from pymongo.database import Database

from sbm_store import edition_games, edition_tables, editions, participants
from sbm_store.swiss_pairing import BLACK, WHITE, Player, pair


def advance(db: Database, edition: dict, now: datetime) -> bool:
    """Pairs the next round when the current one has ended; True once the edition is done."""
    if edition_games.open_games(db, edition["_id"]):
        return False
    gone = set(edition["withdrawn"])
    active = [entry for entry in edition["participants"] if participants.key(entry) not in gone]
    limit = min(edition["settings"]["rounds"], len(edition["participants"]) - 1)
    if edition["round"] >= limit or len(active) < 2:
        return True
    points = {row.key: row.points for row in edition_tables.table(db, edition)}
    players = _players(edition, active, points)
    played = {
        frozenset((pairing["white"], pairing["black"]))
        for planned in edition["rounds"]
        for pairing in planned["pairings"]
    }
    number = edition["round"] + 1
    paired = pair(players, played, first_round=number == 1)
    following = {
        "round": number,
        "bye": paired.bye,
        "pairings": [
            {"board": board, "white": white, "black": black, "match_id": ObjectId()}
            for board, (white, black) in enumerate(paired.pairs, start=1)
        ],
    }
    saved = editions.save_plan(
        db, edition, {"rounds": [*edition["rounds"], following], "round": number}
    )
    if saved is not None:
        edition_games.lay_out(db, saved, now)
    return False


def _players(edition: dict, active: list[dict], points: dict) -> list[Player]:
    whites: dict = {}
    blacks: dict = {}
    last: dict = {}
    byes = set()
    for planned in edition["rounds"]:
        if planned["bye"] is not None:
            byes.add(planned["bye"])
        for pairing in planned["pairings"]:
            whites[pairing["white"]] = whites.get(pairing["white"], 0) + 1
            blacks[pairing["black"]] = blacks.get(pairing["black"], 0) + 1
            last[pairing["white"]] = WHITE
            last[pairing["black"]] = BLACK
    ordered = sorted(
        active, key=lambda entry: (-points.get(participants.key(entry), 0.0), entry["seed"])
    )
    keys = [participants.key(entry) for entry in ordered]
    return [
        Player(
            bot_id=key,
            points=points.get(key, 0.0),
            whites=whites.get(key, 0),
            blacks=blacks.get(key, 0),
            last_color=last.get(key),
            had_bye=key in byes,
        )
        for key in keys
    ]
