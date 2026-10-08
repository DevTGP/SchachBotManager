"""The body of POST /remote/matches: a coder's local bot against a verified bot (E116).

The opponent and a discipline are named as on the website, since the bot's author types them on
the command line; without a discipline the times are free, at most 30 min + 30 s (E115).
"""

import secrets
from dataclasses import dataclass

from pymongo.database import Database
from sbm_store import bots, disciplines
from sbm_store.discipline import Discipline
from sbm_store.names import DISCIPLINES

from sbm_api import body
from sbm_api.errors import invalid_parameter
from sbm_api.play_request import COLORS, free_times

FIELDS = ("opponent", "color", "discipline", "initial_time_ms", "increment_ms")


@dataclass(frozen=True)
class RemoteRequest:
    bot: dict
    color: str
    discipline: Discipline


def parse(db: Database) -> RemoteRequest:
    data = body.json_object(FIELDS)
    name = body.string(data, "opponent", max_length=64)
    bot = bots.by_name(db, name)
    if bot is None:
        raise invalid_parameter("opponent", "opponent is not the name of a verified bot")
    color = body.choice(data, "color", (*COLORS, "random"))
    if color == "random":
        color = secrets.choice(COLORS)
    return RemoteRequest(bot=bot, color=color, discipline=_discipline(db, data))


def _discipline(db: Database, data: dict) -> Discipline:
    if data.get("discipline") is None:
        return free_times(data)
    name = body.string(data, "discipline", max_length=40)
    stored = db[DISCIPLINES].find_one({"name_key": disciplines.name_key(name), "archived": False})
    if stored is None:
        raise invalid_parameter("discipline", "discipline is not the name of a discipline in use")
    for field in ("initial_time_ms", "increment_ms"):
        if field in data:
            raise invalid_parameter(field, f"{field} is part of the discipline")
    return disciplines.snapshot(stored)
