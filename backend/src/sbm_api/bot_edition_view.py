"""An edition of one bot version as the API shows it (schema BotEdition, E180)."""

from sbm_store import editions
from sbm_store.bot_editions import BotEdition

from sbm_api.timestamps import optional_timestamp, timestamp


def bot_edition_view(found: BotEdition, bot_id) -> dict:
    edition = found.edition
    settings = edition["settings"]
    entry = editions.participant(edition, bot_id)
    return {
        "edition_id": str(edition["_id"]),
        "tournament_id": str(edition["tournament_id"]),
        "tournament_name": settings["tournament_name"],
        "number": edition["number"],
        "format": settings["format"],
        "status": edition["status"],
        "started_at": timestamp(edition["started_at"]),
        "finished_at": optional_timestamp(edition["finished_at"]),
        "seed": entry["seed"],
        "participants": found.participants,
        "place": found.place,
        "points": found.points,
        "withdrawn": found.withdrawn,
    }
