"""GET /health: the API answers and reaches the database."""

from flask import Blueprint

from sbm_api import context

blueprint = Blueprint("health", __name__)


@blueprint.get("/health")
def get_health():
    # A failed ping raises ConnectionFailure, which the error handler turns into 503.
    context.db().command("ping")
    return {"status": "ok"}
