"""Checking a name and password, and opening a session (E84).

A number of wrong passwords in a row (a setting, five by default, E154) lock the account for
15 minutes; during the lock even the right password is refused, so guessing cannot continue.
"""

from datetime import datetime, timedelta

from pymongo.database import Database
from sbm_store import account_settings, sessions, users

from sbm_api import passwords, session_cookie
from sbm_api.errors import invalid_credentials, too_many_attempts

LOCK = timedelta(minutes=15)


def authenticate(db: Database, username: str, password: str, now: datetime) -> dict:
    """The account, or an error that does not reveal whether the name exists."""
    user = users.by_username(db, username)
    if user is None:
        passwords.verify_nothing(password)
        raise invalid_credentials()
    locked_until = user["locked_until"]
    if locked_until is not None and locked_until > now:
        raise too_many_attempts(now, locked_until)
    if not passwords.verify(user["password_hash"], password):
        failures = users.count_failed_login(db, user["_id"])
        if failures >= account_settings.get(db).login_failures:
            users.lock(db, user["_id"], now + LOCK)
        raise invalid_credentials()
    if not user["active"]:
        raise invalid_credentials()
    if passwords.needs_rehash(user["password_hash"]):
        users.set_password_hash(db, user["_id"], passwords.hash_password(password))
    return user


def open_session(db: Database, user: dict, now: datetime) -> str:
    """Records the login and returns the token for the cookie."""
    users.record_login(db, user["_id"], now)
    return sessions.create(db, user["_id"], now=now, expires_at=now + session_cookie.LIFETIME)
