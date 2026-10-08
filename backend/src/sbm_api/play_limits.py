"""Limits of interactive games (E115): places in total, and games at once and per day for each
address, account and API token on its own.

The daily counters count only accepted games: a refused request gives its counts back.
"""

import hashlib
from datetime import timedelta

from flask import request
from sbm_store import play, play_settings, rate_limits

from sbm_api import context
from sbm_api.errors import no_capacity, too_many_attempts, too_many_games

DAY = timedelta(days=1)


def ip_key() -> str:
    """The client address as a hash, so stored matches do not keep it."""
    return hashlib.sha256(f"sbm-play:{request.remote_addr}".encode()).hexdigest()[:32]


def check_and_count(origin: dict) -> None:
    """Raises no_capacity, too_many_games or too_many_attempts; otherwise counts the game."""
    db, now = context.db(), context.now()
    settings = play_settings.get(db)
    if play.active_count(db) >= settings.max_games:
        raise no_capacity()
    clients = [(field, value) for field, value in origin.items() if value is not None]
    for field, value in clients:
        if play.active_by(db, field, value) >= settings.games_per_client:
            raise too_many_games()
    counted = []
    for field, value in clients:
        key = f"play:{field}:{value}"
        count = rate_limits.hit(db, key, now=now, window=DAY)
        counted.append(key)
        if count.requests > settings.games_per_day:
            for done in counted:
                rate_limits.give_back(db, done, now=now, window=DAY, amount=1)
            raise too_many_attempts(now, count.resets_at)
