"""The bodies of POST and PATCH /admin/leagues (E131)."""

from pymongo.database import Database
from sbm_store import disciplines, leagues
from sbm_store.league_table import TIEBREAKS

from sbm_api import body
from sbm_api.discipline_request import name
from sbm_api.errors import invalid_parameter

# The ranges of the whole-number settings, as in the schema LeagueSettings.
LIMITS = {
    "tiers": (1, 10),
    "tier_size": (2, 32),
    "games_per_pairing": (1, 10),
    "promotions": (0, 16),
    "min_participants": (2, 320),
    "pause_minutes": (0, 43_200),
    "priority": (0, 1000),
}
MAX_POINTS = 10
MAX_TIEBREAKS = 4
FIELDS = ("name", *leagues.SETTINGS)


def parse_new(db: Database) -> dict:
    """name, discipline_id and the settings given; the store adds the defaults."""
    data = body.json_object(FIELDS)
    if "name" not in data or "discipline_id" not in data:
        raise invalid_parameter("body", "name and discipline_id are required")
    fields = _settings(db, data)
    _check_promotions(leagues.DEFAULTS | fields)
    return fields


def parse_update(db: Database, league: dict) -> dict:
    """The fields to change, at least one; checked together with the league's other settings."""
    data = body.json_object((*FIELDS, "archived"))
    if not data:
        raise invalid_parameter("body", "change at least one field")
    fields = _settings(db, data)
    if "archived" in data:
        fields["archived"] = body.boolean(data, "archived")
    _check_promotions(league | fields)
    return fields


def _settings(db: Database, data: dict) -> dict:
    fields: dict = {}
    if "name" in data:
        fields["name"] = name(data)
    if "discipline_id" in data:
        fields["discipline_id"] = _discipline(db, data)
    for field, (low, high) in LIMITS.items():
        if field in data:
            fields[field] = body.integer(data, field, low=low, high=high)
    if "points" in data:
        fields["points"] = _points(data["points"])
    if "tiebreaks" in data:
        fields["tiebreaks"] = _tiebreaks(data["tiebreaks"])
    return fields


def _discipline(db: Database, data: dict):
    discipline = disciplines.get(db, body.identifier(data, "discipline_id"))
    if discipline is None or discipline["archived"]:
        raise invalid_parameter("discipline_id", "discipline_id is not a discipline in use")
    return discipline["_id"]


def _points(value) -> dict:
    message = (
        f"points needs win, draw and loss from 0 to {MAX_POINTS} in steps of 0.5, "
        "win above loss and win ≥ draw ≥ loss"
    )
    if not isinstance(value, dict) or set(value) != {"win", "draw", "loss"}:
        raise invalid_parameter("points", message)
    for score in value.values():
        if isinstance(score, bool) or not isinstance(score, int | float):
            raise invalid_parameter("points", message)
        if not 0 <= score <= MAX_POINTS or (score * 2) % 1 != 0:
            raise invalid_parameter("points", message)
    win, draw, loss = value["win"], value["draw"], value["loss"]
    if not win > loss or not win >= draw >= loss:
        raise invalid_parameter("points", message)
    return {"win": win, "draw": draw, "loss": loss}


def _tiebreaks(value) -> list[str]:
    message = f"tiebreaks takes up to {MAX_TIEBREAKS} of {', '.join(TIEBREAKS)}, each once"
    if (
        not isinstance(value, list)
        or len(value) > MAX_TIEBREAKS
        or any(item not in TIEBREAKS for item in value)
        or len(set(value)) != len(value)
    ):
        raise invalid_parameter("tiebreaks", message)
    return value


def _check_promotions(settings: dict) -> None:
    if settings["promotions"] * 2 > settings["tier_size"]:
        raise invalid_parameter("promotions", "promotions may be at most half the tier size")
