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
    enqueued = enqueue_request.enqueue(db, order, now=now, created_by=admin["_id"])
    details = {
        "white": order.white["name"],
        "black": order.black["name"],
        "discipline": order.discipline.name,
        "games": order.games,
        "rated": order.rated,
    }
    admin_audit.record(admin, "match.enqueue", None, details)
    return enqueued.response(), 201
