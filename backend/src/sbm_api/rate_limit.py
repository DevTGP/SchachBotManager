"""Limits on attempts with passwords and links per client address (E84), on uploads and on
games set by coders; the limits of coders are settings (E154).

Login, redeeming links and changing the password share one counter, so a guesser gains nothing
by switching between them. The address comes from the proxies in front (SBM_PROXY_HOPS).
"""

from datetime import timedelta

from flask import request
from sbm_store import coder_settings, rate_limits

from sbm_api import context
from sbm_api.errors import too_many_attempts

WINDOW = timedelta(minutes=15)
LIMIT = 30


def count_attempt() -> None:
    now = context.now()
    count = rate_limits.hit(context.db(), f"auth:{request.remote_addr}", now=now, window=WINDOW)
    if count.requests > LIMIT:
        raise too_many_attempts(now, count.resets_at)


UPLOAD_WINDOW = timedelta(days=1)


def count_upload(user: dict) -> None:
    """Uploads per account, since each costs a verification (E92)."""
    db, now = context.db(), context.now()
    key = f"upload:{user['_id']}"
    count = rate_limits.hit(db, key, now=now, window=UPLOAD_WINDOW)
    if count.requests > coder_settings.get(db).uploads_per_day:
        raise too_many_attempts(now, count.resets_at)


GAMES_WINDOW = timedelta(days=1)


def count_games(user: dict, games: int) -> None:
    """Games an account sets through POST /matches (E98); a refused request costs nothing."""
    db, now = context.db(), context.now()
    key = f"matches:{user['_id']}"
    count = rate_limits.hit(db, key, now=now, window=GAMES_WINDOW, amount=games)
    if count.requests > coder_settings.get(db).games_per_day:
        rate_limits.give_back(db, key, now=now, window=GAMES_WINDOW, amount=games)
        raise too_many_attempts(now, count.resets_at)
