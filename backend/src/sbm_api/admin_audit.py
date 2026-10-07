"""Records what an admin did through the API in the audit log (E85)."""

from bson import ObjectId
from sbm_store import audit

from sbm_api import context


def record(admin: dict, action: str, target: ObjectId | str | None, details: dict) -> None:
    audit.record(
        context.db(),
        actor_id=admin["_id"],
        actor=admin["username"],
        action=action,
        target=target,
        details=details,
        now=context.now(),
    )
