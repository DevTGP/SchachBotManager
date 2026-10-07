"""PUT /account/password: change the own password; other sessions end (E84)."""

from flask import Blueprint
from sbm_store import sessions, users

from sbm_api import account_rules, body, context, passwords, rate_limit
from sbm_api.current_user import current_session_id, require_user
from sbm_api.errors import invalid_credentials

blueprint = Blueprint("account", __name__)


@blueprint.put("/account/password")
def change_password():
    user = require_user()
    rate_limit.count_attempt()
    data = body.json_object(("current_password", "new_password"))
    current = body.string(data, "current_password", max_length=128)
    new = account_rules.new_password(data, "new_password")
    if not passwords.verify(user["password_hash"], current):
        raise invalid_credentials()
    db = context.db()
    users.set_password_hash(db, user["_id"], passwords.hash_password(new))
    sessions.delete_for_user(db, user["_id"], keep=current_session_id())
    return "", 204
