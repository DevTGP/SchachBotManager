"""The bodies of POST and PATCH /admin/tournaments (E172)."""

from pymongo.database import Database
from sbm_store import tournaments
from sbm_store.league_table import EDITION_TIEBREAKS

from sbm_api import body, recurrence_request
from sbm_api.discipline_request import name
from sbm_api.errors import invalid_parameter
from sbm_api.league_request import discipline_in_use, tiebreak_list

# The ranges of the whole-number settings, as in the schema TournamentSettings.
LIMITS = {
    "games_per_pairing": (1, 10),
    "rounds": (1, 20),
    "tiebreak_pairs": (0, 5),
    "min_participants": (2, 1024),
    "priority": (0, 1000),
    "ready_hours": (1, 336),
}
MAX_TIEBREAKS = 5
# The format is fixed once the tournament exists.
CHANGEABLE = (
    "name",
    *(field for field in tournaments.SETTINGS if field != "format"),
    "recurrence",
)


def parse_new(db: Database) -> dict:
    """name, discipline_id, format and the settings given; the store adds the defaults."""
    data = body.json_object((*CHANGEABLE, "format"))
    if "name" not in data or "discipline_id" not in data or "format" not in data:
        raise invalid_parameter("body", "name, discipline_id and format are required")
    return {"format": body.choice(data, "format", tournaments.FORMATS)} | _settings(db, data)


def parse_update(db: Database) -> dict:
    """The fields to change, at least one."""
    data = body.json_object((*CHANGEABLE, "archived"))
    if not data:
        raise invalid_parameter("body", "change at least one field")
    fields = _settings(db, data)
    if "archived" in data:
        fields["archived"] = body.boolean(data, "archived")
    return fields


def _settings(db: Database, data: dict) -> dict:
    fields: dict = {}
    if "name" in data:
        fields["name"] = name(data)
    if "discipline_id" in data:
        fields["discipline_id"] = discipline_in_use(db, data, "discipline_id")
    for field, (low, high) in LIMITS.items():
        if field in data:
            fields[field] = body.integer(data, field, low=low, high=high)
    if "tiebreaks" in data:
        fields["tiebreaks"] = tiebreak_list(data["tiebreaks"], EDITION_TIEBREAKS, MAX_TIEBREAKS)
    if "tiebreak_discipline_id" in data:
        fields["tiebreak_discipline_id"] = (
            None
            if data["tiebreak_discipline_id"] is None
            else discipline_in_use(db, data, "tiebreak_discipline_id")
        )
    if "recurrence" in data:
        fields["recurrence"] = recurrence_request.parse(data["recurrence"])
    return fields
