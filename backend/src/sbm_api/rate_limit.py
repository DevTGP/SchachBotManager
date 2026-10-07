"""Limit on attempts with passwords and links per client address (E84).

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
