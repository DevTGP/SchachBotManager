"""Admin: pause and resume the queue; running matches finish (E13, E85)."""

from flask import Blueprint
from sbm_store import queue_settings

from sbm_api import admin_audit, body, context
from sbm_api.current_user import require_admin

blueprint = Blueprint("admin_queue", __name__)


@blueprint.patch("/admin/queue")
def update_queue():
    admin = require_admin()
    paused = body.boolean(body.json_object(("paused",)), "paused")
    queue_settings.set_paused(context.db(), paused)
    admin_audit.record(admin, "queue.pause", None, {"paused": paused})
    return {"paused": paused}
