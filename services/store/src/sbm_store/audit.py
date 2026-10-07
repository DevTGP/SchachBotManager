"""The audit_log collection: who did what as admin, and when (E85)."""

from datetime import datetime

from bson import ObjectId
from pymongo.database import Database

from sbm_store.names import AUDIT_LOG

# The actor of actions from the command line, such as the first invite.
CLI = "cli"


def record(
    db: Database,
    *,
    actor_id: ObjectId | None,
    actor: str,
    action: str,
    target: ObjectId | str | None,
    details: dict | None = None,
    now: datetime,
) -> None:
    db[AUDIT_LOG].insert_one(
        {
            "at": now,
            "actor_id": actor_id,
            "actor": actor,
            "action": action,
            "target": target,
            "details": details or {},
        }
    )
