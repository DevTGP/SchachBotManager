"""The league and tournament games of an account that have not ended (E186).

Released games come first, by deadline; then the waiting ones in the order release hands them
out (competition_readiness.ORDER).
"""

from bson import ObjectId
from pymongo.database import Database

from sbm_store import competition_readiness, matches
from sbm_store.names import MATCHES


def of_account(db: Database, user_id: ObjectId) -> list[dict]:
    """Summaries of the account's open competition games."""
    query = {
        "type": {"$in": list(competition_readiness.COMPETITIONS)},
        "status": {"$in": [matches.QUEUED, matches.RUNNING]},
        "$or": [{f"{color}.user_id": user_id} for color in ("white", "black")],
    }
    projection = matches.SUMMARY_PROJECTION | {"context": 1}
    released = list(
        db[MATCHES]
        .find(query | {"readiness": {"$ne": None}}, projection)
        .sort([("readiness.deadline", 1), ("_id", 1)])
    )
    waiting = list(
        db[MATCHES].find(query | {"readiness": None}, projection).sort(competition_readiness.ORDER)
    )
    return released + waiting
