"""PATCH /bots/{bot_id}: the owner changes the description or retires the bot (E95, E96)."""

from flask import Blueprint
from sbm_store import bots

from sbm_api import body, bot_description, context
from sbm_api.bot_access import owned_bot
from sbm_api.bot_view import bot_detail_view
from sbm_api.current_user import require_coder
from sbm_api.errors import invalid_parameter
from sbm_api.params import object_id

blueprint = Blueprint("own_bot", __name__)


@blueprint.patch("/bots/<bot_id>")
def update_own_bot(bot_id: str):
    """An admin's block stays: a disabled bot cannot switch, only its description changes."""
    user = require_coder()
    db = context.db()
    bot = owned_bot(bots.get(db, object_id(bot_id, "bot_id")), user)
    data = body.json_object(("description", "status"))
    if not data:
        raise invalid_parameter("body", "send a description or a status")
    description = bot_description.check(data["description"]) if "description" in data else None
    retired = None
    if "status" in data:
        retired = body.choice(data, "status", (bots.VERIFIED, bots.RETIRED)) == bots.RETIRED
    changed = bots.change_by_owner(db, bot["_id"], description=description, retired=retired)
    if changed is None:
        raise invalid_parameter("status", f"a {bot['status']} bot cannot switch")
    return bot_detail_view(changed, user)
