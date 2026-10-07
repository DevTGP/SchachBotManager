"""POST /invites/redeem: an invite link becomes an account, which is then logged in (E83)."""

from flask import Blueprint, make_response
from sbm_store import invites, users

from sbm_api import account_rules, body, context, passwords, rate_limit, session_cookie
from sbm_api.errors import USERNAME_TAKEN, ApiError, invalid_token
from sbm_api.login import open_session
from sbm_api.user_view import session_view

blueprint = Blueprint("invites", __name__)


@blueprint.post("/invites/redeem")
def redeem_invite():
    rate_limit.count_attempt()
    data = body.json_object(("token", "username", "password"))
    token = account_rules.token(data)
    username = account_rules.username(data)
    password = account_rules.new_password(data, "password")
    db, now = context.db(), context.now()
    # Checked first, so a taken name does not use up the invite even for a moment.
    if users.username_taken(db, username):
        raise _username_taken()
    invite = invites.claim(db, token, now)
    if invite is None:
        raise invalid_token()
    user = users.new_user(
        username,
        passwords.hash_password(password),
        invite["role"],
        invited_by=invite["created_by"],
        now=now,
    )
    if not users.insert(db, user):
        # Someone took the name in between; the invite stays usable.
        invites.release(db, invite["_id"])
        raise _username_taken()
    invites.mark_used_by(db, invite["_id"], user["_id"])
    response = make_response(session_view(user), 201)
    session_cookie.put(response, open_session(db, user, now))
    return response


def _username_taken() -> ApiError:
    return ApiError(409, USERNAME_TAKEN, "the name is taken", "username")
