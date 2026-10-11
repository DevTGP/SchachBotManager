"""The tournament editions a bot version played in, with its place there (E180)."""

from dataclasses import dataclass

from bson import ObjectId
from pymongo import DESCENDING
from pymongo.database import Database

from sbm_store import edition_tables, editions, tournaments
from sbm_store.names import EDITIONS


@dataclass
class BotEdition:
    edition: dict
    participants: int
    # The rank in the table or the place reached in knockout; None while open or after
    # withdrawing.
    place: int | None
    # The points in the table; None in knockout.
    points: float | None
    withdrawn: bool


def of_bot(db: Database, bot_id: ObjectId) -> list[BotEdition]:
    """The started editions with the bot among the participants, newest first."""
    query = {
        "participants.bot_id": bot_id,
        "status": {"$in": [editions.RUNNING, editions.FINISHED]},
    }
    found = db[EDITIONS].find(query).sort([("started_at", DESCENDING), ("_id", DESCENDING)])
    return [_entry(db, edition, bot_id) for edition in found]


def _entry(db: Database, edition: dict, bot_id: ObjectId) -> BotEdition:
    count = len(edition["participants"])
    if edition["settings"]["format"] == tournaments.KNOCKOUT:
        places = (edition["final"] or {}).get("placements") or edition_tables.placements(edition)
        mine = next(each for each in places if each["bot"]["bot_id"] == bot_id)
        return BotEdition(edition, count, mine["place"], None, mine["withdrawn"])
    rows = (edition["final"] or {}).get("table") or [
        row.to_edition_document() for row in edition_tables.table(db, edition)
    ]
    row = next(each for each in rows if each["bot"]["bot_id"] == bot_id)
    return BotEdition(edition, count, row["rank"], row["points"], row["withdrawn"])
