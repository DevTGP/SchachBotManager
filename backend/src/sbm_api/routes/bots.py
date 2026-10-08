"""GET /bots and /bots/{bot_id}: verified bots for everyone (E15); POST /bots: upload (E91)."""

from bson import ObjectId
from flask import Blueprint
from sbm_store import bot_files, bots, jobs, versions

from sbm_api import context, rate_limit
from sbm_api.bot_view import bot_detail_view, bot_view, may_see_details
from sbm_api.current_user import current_user, require_user
from sbm_api.errors import (
    NAME_TAKEN,
    UPLOAD_CONFLICT,
    ApiError,
    invalid_parameter,
    not_found,
)
from sbm_api.params import object_id
from sbm_api.upload_request import parse_upload

blueprint = Blueprint("bots", __name__)


@blueprint.get("/bots")
def list_bots():
    items = [bot for bot in bots.all_by_name(context.db()) if bot["status"] == bots.VERIFIED]
    return {"items": [bot_view(bot) for bot in items]}


@blueprint.get("/bots/<bot_id>")
def get_bot(bot_id: str):
    bot = bots.get(context.db(), object_id(bot_id, "bot_id"))
    viewer = current_user()
    if bot is None or (bot["status"] not in bots.PUBLIC and not may_see_details(bot, viewer)):
        raise not_found("no such bot")
    return bot_detail_view(bot, viewer)


@blueprint.post("/bots")
def upload_bot():
    """A new bot, or a new version of an own one; the runner verifies it (E92)."""
    user = require_user()
    upload = parse_upload()
    db, now = context.db(), context.now()
    previous = bots.latest(db, upload.name)
    if previous is not None:
        if bots.is_builtin(previous) or previous.get("owner_id") != user["_id"]:
            raise ApiError(409, NAME_TAKEN, "the name belongs to another bot", "name")
        if versions.parse(upload.version) <= versions.parse(previous["version"]):
            raise invalid_parameter("version", f"version must be higher than {previous['version']}")
    # Counted once the request is valid, so a mistake does not cost an upload.
    rate_limit.count_upload(user)
    bot_id = ObjectId()
    entries = bot_files.store_files(db, bot_id, upload.files)
    bot = bots.new_uploaded_bot(
        bot_id=bot_id,
        name=upload.name,
        version=upload.version,
        language=upload.language,
        entry=upload.entry,
        files=entries,
        source_hash=bot_files.source_hash(entries),
        owner_id=user["_id"],
        previous=previous,
        now=now,
    )
    if not bots.insert(db, bot):
        bot_files.delete_files(db, entries)
        raise ApiError(409, UPLOAD_CONFLICT, "another upload of this name came first", "name")
    jobs.insert(db, jobs.new_verification_job(bot_id, now=now))
    return bot_detail_view(bot, user), 201
