"""Application factory; gunicorn loads sbm_api.wsgi:app."""

import os
from collections.abc import Callable
from datetime import UTC, datetime

from flask import Flask
from pymongo.database import Database
from sbm_store.connection import database_from_env
from werkzeug.middleware.proxy_fix import ProxyFix

from sbm_api import csrf, current_user
from sbm_api.errors import register_error_handlers
from sbm_api.routes import (
    account,
    account_bots,
    account_rating,
    account_tokens,
    admin_audit_log,
    admin_bots,
    admin_disciplines,
    admin_invites,
    admin_match_actions,
    admin_matches,
    admin_play,
    admin_queue,
    admin_users,
    bot_source,
    bots,
    disciplines,
    health,
    invites,
    matches,
    own_bot,
    own_matches,
    password_resets,
    play,
    queue,
    ratings,
    remote,
    session,
)

API_PREFIX = "/api/v1"
PUBLIC_URL_VARIABLE = "SBM_PUBLIC_URL"
PROXY_HOPS_VARIABLE = "SBM_PROXY_HOPS"
BLUEPRINTS = (
    health,
    matches,
    own_matches,
    play,
    bots,
    own_bot,
    bot_source,
    queue,
    disciplines,
    ratings,
    session,
    invites,
    password_resets,
    account,
    account_rating,
    account_bots,
    account_tokens,
    remote,
    admin_users,
    admin_invites,
    admin_bots,
    admin_disciplines,
    admin_matches,
    admin_match_actions,
    admin_play,
    admin_queue,
    admin_audit_log,
)


def utc_now() -> datetime:
    return datetime.now(UTC)


def create_app(
    db: Database | None = None,
    *,
    now: Callable[[], datetime] = utc_now,
    public_url: str | None = None,
    proxy_hops: int | None = None,
) -> Flask:
    """Without db the connection comes from SBM_MONGO_URI and SBM_MONGO_DB."""
    app = Flask(__name__)
    app.json.sort_keys = False
    app.extensions["sbm"] = {
        "db": db if db is not None else database_from_env(os.environ),
        "now": now,
        # The PGN Site tag and the base of one-time links; configuration, not code.
        "public_url": public_url or os.environ.get(PUBLIC_URL_VARIABLE) or "?",
    }
    # The client address for rate limits, from the proxies in front of the API (E84).
    hops = proxy_hops if proxy_hops is not None else int(os.environ.get(PROXY_HOPS_VARIABLE, 0))
    if hops > 0:
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=hops, x_proto=0)
    for module in BLUEPRINTS:
        app.register_blueprint(module.blueprint, url_prefix=API_PREFIX)
    csrf.register(app)
    current_user.register(app)
    register_error_handlers(app)
    return app
