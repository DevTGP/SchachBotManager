"""Limits on attempts with passwords and links per client address (E84) and on uploads.

Login, redeeming links and changing the password share one counter, so a guesser gains nothing
by switching between them. The address comes from the proxies in front (SBM_PROXY_HOPS).
"""

from datetime import timedelta

from flask import request
from sbm_store import rate_limits

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
UPLOAD_LIMIT = 20


def count_upload(user: dict) -> None:
    """Uploads per account, since each costs a verification (E92)."""
    now = context.now()
    key = f"upload:{user['_id']}"
    count = rate_limits.hit(context.db(), key, now=now, window=UPLOAD_WINDOW)
    if count.requests > UPLOAD_LIMIT:
        raise too_many_attempts(now, count.resets_at)
