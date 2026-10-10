"""Settings for invitations and logins in the settings collection (E154).

An invitation link is valid for invite_days unless the admin picks another number up to
invite_max_days (E83); after login_failures wrong passwords in a row the login of an account
is locked for a while (E84).
"""

from dataclasses import dataclass

from pymongo.database import Database

from sbm_store import settings_document

DOCUMENT_ID = "accounts"
# Inclusive ranges the web API accepts.
LIMITS = {"invite_days": (1, 365), "invite_max_days": (1, 365), "login_failures": (1, 100)}


@dataclass(frozen=True)
class AccountSettings:
    invite_days: int = 7
    invite_max_days: int = 30
    login_failures: int = 5


def get(db: Database) -> AccountSettings:
    return settings_document.load(db, DOCUMENT_ID, AccountSettings)


def problem(settings: AccountSettings) -> str | None:
    """The field that does not fit the others; None if all fit."""
    if settings.invite_days > settings.invite_max_days:
        return "invite_days"
    return None


def save(db: Database, settings: AccountSettings) -> None:
    settings_document.store(db, DOCUMENT_ID, settings)
