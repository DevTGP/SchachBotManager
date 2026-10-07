"""POST /password-resets/redeem: a reset link sets a new password and logs in (E83).

All other sessions of the account end, in case someone else knew the old password.
"""

from flask import Blueprint, make_response
from sbm_store import password_resets, sessions, users

from sbm_api import account_rules, body, context, passwords, rate_limit, session_cookie
from sbm_api.errors import invalid_token
from sbm_api.login import open_session
from sbm_api.user_view import session_view

blueprint = Blueprint("password_resets", __name__)


@blueprint.post("/password-resets/redeem")
def redeem_password_reset():
    rate_limit.count_attempt()
    data = body.json_object(("token", "password"))
    token = account_rules.token(data)
    password = account_rules.new_password(data, "password")
    db, now = context.db(), context.now()
    reset = password_resets.redeem(db, token, now)
    user = None if reset is None else users.get(db, reset["user_id"])
    if user is None or not user["active"]:
        raise invalid_token()
    users.set_password_hash(db, user["_id"], passwords.hash_password(password))
    sessions.delete_for_user(db, user["_id"])
    response = make_response(session_view(user))
    session_cookie.put(response, open_session(db, user, now))
    return response
