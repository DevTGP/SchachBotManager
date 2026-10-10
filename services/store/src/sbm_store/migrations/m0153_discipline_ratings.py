"""Ratings per discipline (E163): the single values go, counted matches are counted again.

The matches keep what they need: the recount (E105) puts each into its discipline. Without a
counted match there is nothing to recount, so a new database gets no request.
"""

from datetime import UTC, datetime

from pymongo.database import Database

from sbm_store import rating_recount
from sbm_store.names import BOTS, MATCHES, USERS

OLD_INDEX = "rating.value_-1"


def apply(db: Database) -> None:
    if OLD_INDEX in db[BOTS].index_information():
        db[BOTS].drop_index(OLD_INDEX)
    for collection in (BOTS, USERS):
        db[collection].update_many({"rating": {"$exists": True}}, {"$unset": {"rating": ""}})
    if db[MATCHES].count_documents({"rating": {"$exists": True}}, limit=1):
        rating_recount.request(db, datetime.now(UTC))
