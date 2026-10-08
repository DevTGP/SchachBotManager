"""The account behind the session cookie, loaded once per request (E84).

The role and the active flag come from the database on every request, so changes apply at once.
A session in use is extended at most once a day; the cookie then gets the new lifetime too.
"""

from datetime import timedelta

from flask import Flask, Response, g
from sbm_store import sessions, users

from sbm_api import context, session_cookie
from sbm_api.errors import forbidden, unauthenticated

REFRESH_AFTER = timedelta(days=1)
_UNSET = object()


def current_user() -> dict | None:
    user = g.get("sbm_user", _UNSET)
    if user is _UNSET:
        user = _load()
        g.sbm_user = user
    return user


def current_session_id() -> str | None:
    current_user()
    return g.get("sbm_session_id")


def require_user() -> dict:
    user = current_user()
    if user is None:
        raise unauthenticated()
    return user


def require_coder() -> dict:
    """Coders and admins: own bots, their games and API tokens; players only play (E103)."""
    user = require_user()
    if user["role"] not in (users.CODER, users.ADMIN):
        raise forbidden("only coders may do this")
    return user


def require_admin() -> dict:
    user = require_user()
    if user["role"] != users.ADMIN:
        raise forbidden("only admins may do this")
    return user


def register(app: Flask) -> None:
    @app.after_request
    def refresh_cookie(response: Response) -> Response:
        token = g.get("sbm_refresh_token")
        if token is not None and session_cookie.NAME not in _cookies_set(response):
            session_cookie.put(response, token)
        return response


def _load() -> dict | None:
    token = session_cookie.read()
    if not token:
        return None
    db, now = context.db(), context.now()
    session = sessions.find(db, token, now)
    if session is None:
        return None
    user = users.get(db, session["user_id"])
    if user is None or not user["active"]:
        return None
    g.sbm_session_id = session["_id"]
    if session["expires_at"] - now < session_cookie.LIFETIME - REFRESH_AFTER:
        sessions.extend(db, session["_id"], now + session_cookie.LIFETIME)
        g.sbm_refresh_token = token
    return user


def _cookies_set(response: Response) -> set[str]:
    return {header.split("=", 1)[0] for header in response.headers.getlist("Set-Cookie")}
