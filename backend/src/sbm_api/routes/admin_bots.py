"""Admin: disable a verified bot or enable a disabled one again (E93, E85)."""

from flask import Blueprint
from sbm_store import bots

from sbm_api import admin_audit, body, context
from sbm_api.bot_view import bot_detail_view
from sbm_api.current_user import require_admin
from sbm_api.errors import invalid_parameter, not_found
from sbm_api.params import object_id

blueprint = Blueprint("admin_bots", __name__)


@blueprint.patch("/admin/bots/<bot_id>")
def update_bot(bot_id: str):
    admin = require_admin()
    target = object_id(bot_id, "bot_id")
    data = body.json_object(("status",))
    status = body.choice(data, "status", (bots.VERIFIED, bots.DISABLED))
    db = context.db()
    bot = bots.set_enabled(db, target, status == bots.VERIFIED)
    if bot is None:
        if bots.get(db, target) is None:
            raise not_found("no such bot")
        raise invalid_parameter("status", "only verified and disabled bots can be switched")
    admin_audit.record(admin, "bot.update", target, {"status": status})
    return bot_detail_view(bot, admin)
