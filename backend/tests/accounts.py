"""Accounts written through the store, and a clock the tests can move."""

from datetime import datetime, timedelta

from sbm_store import users

from sbm_api import passwords

from stored_games import NOW

CSRF = {"X-SBM-CSRF": "1"}
PASSWORD = "correct horse battery"


class Clock:
    def __init__(self, start: datetime) -> None:
        self.current = start

    def now(self) -> datetime:
        return self.current

    def advance(self, delta: timedelta) -> None:
        self.current += delta


def add_user(db, username: str, role: str = users.CODER, *, active: bool = True):
    """Returns the stored user and its password."""
    user = users.new_user(
        username, passwords.hash_password(PASSWORD), role, invited_by=None, now=NOW
    )
    user["active"] = active
    assert users.insert(db, user)
    return user, PASSWORD
