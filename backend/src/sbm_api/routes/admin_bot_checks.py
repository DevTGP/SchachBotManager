"""Admin: check bots again with the current rules, or verify a rejected bot anyway (E153).

A recheck only adds a report; the bot keeps its status and its upload report. The runner does
the work, the API only queues the job.
"""

from flask import Blueprint
from sbm_store import bots, rechecks

from sbm_api import admin_audit, body, context
from sbm_api.bot_view import bot_detail_view
from sbm_api.current_user import require_admin
from sbm_api.errors import BOT_STATE, BOT_VERIFYING, BUILTIN_BOT, ApiError, not_found
from sbm_api.params import object_id

blueprint = Blueprint("admin_bot_checks", __name__)

# All languages of the bot API; those without uploads yet simply have no bot to check.
LANGUAGES = ("python", "cpp", "java", "csharp", "javascript")


@blueprint.post("/admin/bots/recheck")
def recheck_language():
    admin = require_admin()
    language = body.choice(body.json_object(("language",)), "language", LANGUAGES)
    queued = rechecks.request_language(context.db(), language, context.now())
    admin_audit.record(
        admin, "bot.recheck_language", None, {"language": language, "queued": queued}
    )
    return {"queued": queued}, 202


@blueprint.post("/admin/bots/<bot_id>/recheck")
def recheck_bot(bot_id: str):
    admin = require_admin()
    db = context.db()
    bot = _bot(bot_id)
    if bots.is_builtin(bot):
        raise ApiError(409, BUILTIN_BOT, "a reference bot is not checked")
    if bot["status"] not in rechecks.RECHECKABLE or not rechecks.request(
        db, bot["_id"], context.now()
    ):
        raise ApiError(409, BOT_VERIFYING, "a verification of the bot is pending")
    admin_audit.record(admin, "bot.recheck", bot["_id"], {"status": bot["status"]})
    return bot_detail_view(bot, admin), 202


@blueprint.post("/admin/bots/<bot_id>/override")
def override_bot(bot_id: str):
    admin = require_admin()
    bot = _bot(bot_id)
    overridden = bots.override(context.db(), bot["_id"], context.now())
    if overridden is None:
        raise ApiError(409, BOT_STATE, "only a rejected bot can be verified anyway")
    rejection = bot.get("rejection") or {}
    admin_audit.record(admin, "bot.override", bot["_id"], {"stage": rejection.get("stage")})
    return bot_detail_view(overridden, admin)


def _bot(bot_id: str) -> dict:
    bot = bots.get(context.db(), object_id(bot_id, "bot_id"))
    if bot is None:
        raise not_found("no such bot")
    return bot
