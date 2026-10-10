"""The rating of a holder without counted matches, read once per request (E103, E154)."""

from flask import g
from sbm_store import rating_settings

from sbm_api import context


def rating_start() -> int:
    if "rating_start" not in g:
        g.rating_start = rating_settings.get(context.db()).start
    return g.rating_start
