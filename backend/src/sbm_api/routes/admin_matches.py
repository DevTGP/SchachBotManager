"""Admin: queue games between two bots (E71, E85)."""

from flask import Blueprint

from sbm_api import admin_audit, context, enqueue_request
from sbm_api.current_user import require_admin

blueprint = Blueprint("admin_matches", __name__)


@blueprint.post("/admin/matches")
def enqueue_matches():
    admin = require_admin()
    db, now = context.db(), context.now()
    order = enqueue_request.parse(db)
    ids = enqueue_request.enqueue(db, order, now=now)
    details = {
        "white": order.white["name"],
        "black": order.black["name"],
        "discipline": order.discipline.name,
        "games": order.games,
    }
    admin_audit.record(admin, "match.enqueue", None, details)
    return {"match_ids": [str(match_id) for match_id in ids]}, 201
