"""GET /bots/{bot_id}/file and /bots/{bot_id}/source: the uploaded files (E97).

Only for the owner and admins, and always as a download: the bytes never come back as a page
or script of the site's own address. Nothing here runs or unpacks them (E81).
"""

import io
import re
import zipfile

from flask import Blueprint, Response, request
from sbm_store import bot_files, bots

from sbm_api import context
from sbm_api.bot_access import source_bot
from sbm_api.current_user import require_user
from sbm_api.errors import invalid_parameter, not_found
from sbm_api.params import object_id

blueprint = Blueprint("bot_source", __name__)

MAX_PATH_LENGTH = 200
# Fixed, so the same files give the same ZIP file; 1980 is the earliest date ZIP can hold.
ZIP_TIMESTAMP = (1980, 1, 1, 0, 0, 0)
UNSAFE_NAME = re.compile(r"[^A-Za-z0-9._-]")


@blueprint.get("/bots/<bot_id>/file")
def get_bot_file(bot_id: str):
    bot = _bot(bot_id)
    path = request.args.get("path")
    if path is None or len(path) > MAX_PATH_LENGTH:
        raise invalid_parameter("path", f"path is required, at most {MAX_PATH_LENGTH} characters")
    entry = next((entry for entry in bot.get("files", []) if entry["path"] == path), None)
    if entry is None:
        raise not_found("the bot has no such file")
    content = bot_files.read_file(context.db(), entry)
    return _download(content, "application/octet-stream", path.rsplit("/", 1)[-1])


@blueprint.get("/bots/<bot_id>/source")
def get_bot_source(bot_id: str):
    bot = _bot(bot_id)
    entries = bot.get("files", [])
    if not entries:
        # Reference bots are part of the SDK and have no uploaded files (E72).
        raise not_found("the bot has no uploaded files")
    folder = f"{bot['name']}-{bot['version']}"
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        for entry in sorted(entries, key=lambda entry: entry["path"]):
            info = zipfile.ZipInfo(f"{folder}/{entry['path']}", ZIP_TIMESTAMP)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            archive.writestr(info, bot_files.read_file(context.db(), entry))
    return _download(buffer.getvalue(), "application/zip", f"{folder}.zip")


def _bot(bot_id: str) -> dict:
    user = require_user()
    return source_bot(bots.get(context.db(), object_id(bot_id, "bot_id")), user)


def _download(content: bytes, mimetype: str, name: str) -> Response:
    # Names and versions are plain already; the file name is only a suggestion to the browser.
    safe_name = UNSAFE_NAME.sub("_", name) or "file"
    return Response(
        content,
        mimetype=mimetype,
        headers={
            "Content-Disposition": f'attachment; filename="{safe_name}"',
            "X-Content-Type-Options": "nosniff",
            "Cache-Control": "private, no-store",
        },
    )
