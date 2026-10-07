"""GET, POST and DELETE /session: who is logged in, login and logout (E84)."""

from flask import Blueprint, make_response
from sbm_store import sessions

from sbm_api import body, context, rate_limit, session_cookie
from sbm_api.current_user import current_user
from sbm_api.login import authenticate, open_session
from sbm_api.user_view import session_view

blueprint = Blueprint("session", __name__)


@blueprint.get("/session")
def get_session():
    return session_view(current_user())


@blueprint.post("/session")
def login():
    rate_limit.count_attempt()
    data = body.json_object(("username", "password"))
    username = body.string(data, "username", max_length=32)
    password = body.string(data, "password", max_length=128)
    db, now = context.db(), context.now()
    user = authenticate(db, username, password, now)
    response = make_response(session_view(user))
    session_cookie.put(response, open_session(db, user, now))
    return response


@blueprint.delete("/session")
def logout():
    token = session_cookie.read()
    if token:
        sessions.delete(context.db(), token)
    response = make_response("", 204)
    session_cookie.remove(response)
    return response
