"""The numbers of the rating rule in the settings collection (E154).

Changing them asks for a recount of all ratings (E105); the web API does that, so this module
stays below ratings and rating_recount.
"""

from pymongo.database import Database

from sbm_store import settings_document
from sbm_store.rating_rule import RatingRule

DOCUMENT_ID = "rating_rule"
# Inclusive ranges the web API accepts.
LIMITS = {
    "start": (0, 10_000),
    "base": (1, 1000),
    "step": (1, 1000),
    "max_win": (1, 1000),
    "min_win": (0, 1000),
    "max_draw": (0, 1000),
}


def get(db: Database) -> RatingRule:
    return settings_document.load(db, DOCUMENT_ID, RatingRule)


def problem(rule: RatingRule) -> str | None:
    """The field that does not fit the others; None if all fit."""
    if rule.min_win > rule.base:
        return "min_win"
    if rule.base > rule.max_win:
        return "max_win"
    return None


def save(db: Database, rule: RatingRule) -> None:
    settings_document.store(db, DOCUMENT_ID, rule)
