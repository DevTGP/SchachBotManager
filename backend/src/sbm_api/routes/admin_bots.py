"""Admin: disable a verified or retired bot, enable a disabled one again (E93, E96, E85), or
delete one version for good (E105)."""

from flask import Blueprint
from sbm_store import bot_deletion, bots

from sbm_api import admin_audit, body, context
from sbm_api.bot_view import bot_detail_view
from sbm_api.current_user import require_admin
from sbm_api.errors import (
    BOT_PLAYING,
    BOT_VERIFYING,
    BUILTIN_BOT,
    ApiError,
    invalid_parameter,
    not_found,
)
from sbm_api.params import object_id

blueprint = Blueprint("admin_bots", __name__)

NOT_DELETABLE = {
    bot_deletion.BUILTIN: (BUILTIN_BOT, "a reference bot cannot be deleted"),
    bot_deletion.VERIFYING: (BOT_VERIFYING, "the bot is still being verified"),
    bot_deletion.PLAYING: (BOT_PLAYING, "the bot is playing a match"),
}


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
        raise invalid_parameter("status", f"the bot cannot switch to {status}")
    admin_audit.record(admin, "bot.update", target, {"status": status})
    return bot_detail_view(bot, admin)


@blueprint.delete("/admin/bots/<bot_id>")
def delete_bot(bot_id: str):
    admin = require_admin()
    target = object_id(bot_id, "bot_id")
    try:
        deletion = bot_deletion.delete_bot(context.db(), target, context.now())
    except bot_deletion.NotDeletable as error:
        code, message = NOT_DELETABLE[error.reason]
        raise ApiError(409, code, message) from None
    if deletion is None:
        raise not_found("no such bot")
    bot = deletion.bot
    admin_audit.record(
        admin,
        "bot.delete",
        target,
        {"name": bot["name"], "version": bot["version"], "matches": deletion.matches},
    )
    return "", 204
