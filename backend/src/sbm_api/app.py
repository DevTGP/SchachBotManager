"""Application factory; gunicorn loads sbm_api.wsgi:app."""

import os
from collections.abc import Callable
from datetime import UTC, datetime

from flask import Flask
from pymongo.database import Database
from sbm_store.connection import database_from_env

from sbm_api.errors import register_error_handlers
from sbm_api.routes import bots, health, matches, queue

API_PREFIX = "/api/v1"
PUBLIC_URL_VARIABLE = "SBM_PUBLIC_URL"


def utc_now() -> datetime:
    return datetime.now(UTC)


def create_app(
    db: Database | None = None,
    *,
    now: Callable[[], datetime] = utc_now,
    public_url: str | None = None,
) -> Flask:
    """Without db the connection comes from SBM_MONGO_URI and SBM_MONGO_DB."""
    app = Flask(__name__)
    app.json.sort_keys = False
    app.extensions["sbm"] = {
        "db": db if db is not None else database_from_env(os.environ),
        "now": now,
        # The PGN Site tag; the address is configuration, not code.
        "public_url": public_url or os.environ.get(PUBLIC_URL_VARIABLE) or "?",
    }
    for blueprint in (health.blueprint, matches.blueprint, bots.blueprint, queue.blueprint):
        app.register_blueprint(blueprint, url_prefix=API_PREFIX)
    register_error_handlers(app)
    return app
