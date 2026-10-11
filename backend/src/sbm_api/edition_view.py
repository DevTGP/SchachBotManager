"""An edition with its table or bracket as the API shows it (schema Edition, E177, E180).

A running edition computes its table or placements from its matches; a finished one shows the
final result it stored. The counts of games come from the matches either way.
"""

from pymongo.database import Database
from sbm_store import edition_games, edition_tables, matches, tournaments

from sbm_api.edition_bracket_view import bracket_view
from sbm_api.league_view import league_bot
from sbm_api.match_view import discipline
from sbm_api.timestamps import optional_timestamp
from sbm_api.tournament_view import settings_view

OPEN = (matches.QUEUED, matches.RUNNING)


def edition_view(db: Database, edition: dict) -> dict:
    settings = edition["settings"]
    started = settings is not None
    games = edition_games.of_edition(db, edition["_id"]) if started else []
    knockout = started and settings["format"] == tournaments.KNOCKOUT
    return {
        "id": str(edition["_id"]),
        "tournament_id": str(edition["tournament_id"]),
        "tournament_name": _tournament_name(db, edition),
        "number": edition["number"],
        "status": edition["status"],
        "starts_after": optional_timestamp(edition["starts_after"]),
        "started_at": optional_timestamp(edition["started_at"]),
        "finished_at": optional_timestamp(edition["finished_at"]),
        "settings": settings_view(settings) if started else None,
        "discipline": discipline(settings["discipline_snapshot"]) if started else None,
        "tiebreak_discipline": _tiebreak_discipline(settings) if knockout else None,
        "participants": [_participant(edition, entry) for entry in edition["participants"]],
        "round": edition["round"],
        "games": len(games),
        "finished": sum(1 for game in games if game["status"] not in OPEN),
        "table": _table(db, edition, games) if started and not knockout else [],
        "bracket_size": edition["bracket_size"] if knockout else None,
        "bracket": bracket_view(edition, games) if knockout else [],
        "placements": _placements(edition) if knockout else [],
    }


def _tournament_name(db: Database, edition: dict) -> str:
    """The name at the start; before it the tournament's current name."""
    if edition["settings"] is not None:
        return edition["settings"]["tournament_name"]
    tournament = tournaments.get(db, edition["tournament_id"])
    return "?" if tournament is None else tournament["name"]


def _tiebreak_discipline(settings: dict) -> dict:
    """Without a tiebreak discipline the tiebreak games use the tournament's (E176)."""
    snapshot = settings["tiebreak_discipline_snapshot"] or settings["discipline_snapshot"]
    return discipline(snapshot)


def _participant(edition: dict, entry: dict) -> dict:
    return {
        "bot": league_bot(entry),
        "seed": entry["seed"],
        "rating": entry["rating"],
        "withdrawn": entry["bot_id"] in edition["withdrawn"],
    }


def _table(db: Database, edition: dict, games: list[dict]) -> list[dict]:
    final = edition["final"]
    if final is not None:
        rows = final["table"]
    else:
        rows = [row.to_edition_document() for row in edition_tables.table(db, edition, games)]
    return [row | {"bot": league_bot(row["bot"])} for row in rows]


def _placements(edition: dict) -> list[dict]:
    final = edition["final"]
    places = final["placements"] if final is not None else edition_tables.placements(edition)
    return [each | {"bot": league_bot(each["bot"])} for each in places]
