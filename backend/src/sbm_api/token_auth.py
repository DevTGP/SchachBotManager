"""The account behind an API token in the header Authorization: Bearer … (E116).

Only remote matches accept a token; everything else needs the session. The role comes from the
database on every request, so a coder who became a player can no longer use old tokens.
"""

from flask import request
from sbm_store import api_tokens, users

from sbm_api import context
from sbm_api.errors import UNAUTHENTICATED, ApiError, forbidden

SCHEME = "Bearer "


def require_token_user() -> tuple[dict, dict]:
    """The account and the token document; 401 without a valid token, 403 for players."""
    header = request.headers.get("Authorization", "")
    if not header.startswith(SCHEME):
        raise _unauthenticated()
    db, now = context.db(), context.now()
    token = api_tokens.find(db, header[len(SCHEME) :].strip(), now=now)
    user = None if token is None else users.get(db, token["user_id"])
    if user is None or not user["active"]:
        raise _unauthenticated()
    if user["role"] not in (users.CODER, users.ADMIN):
        raise forbidden("only coders may play remote games")
    return user, token


def _unauthenticated() -> ApiError:
    return ApiError(401, UNAUTHENTICATED, "a valid API token is required")
