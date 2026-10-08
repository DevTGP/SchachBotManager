"""Admin: the limits of interactive games (E13, E115)."""

from flask import Blueprint
from sbm_store import play_settings

from sbm_api import admin_audit, body, context
from sbm_api.current_user import require_admin

blueprint = Blueprint("admin_play", __name__)


@blueprint.get("/admin/play-settings")
def get_play_settings():
    require_admin()
    return play_settings.get(context.db()).to_document()


@blueprint.put("/admin/play-settings")
def update_play_settings():
    admin = require_admin()
    data = body.json_object(tuple(play_settings.LIMITS))
    values = {
        name: body.integer(data, name, low=low, high=high)
        for name, (low, high) in play_settings.LIMITS.items()
    }
    settings = play_settings.PlaySettings(**values)
    play_settings.save(context.db(), settings)
    admin_audit.record(admin, "play.settings", None, settings.to_document())
    return settings.to_document()
