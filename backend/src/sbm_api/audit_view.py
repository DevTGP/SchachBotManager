"""Audit log entries as the API shows them (schema AuditEntry, E151)."""

from datetime import datetime

from bson import ObjectId

from sbm_api.timestamps import timestamp


def audit_view(entry: dict) -> dict:
    target = entry["target"]
    return {
        "id": str(entry["_id"]),
        "at": timestamp(entry["at"]),
        "actor": entry["actor"],
        "action": entry["action"],
        "target": None if target is None else str(target),
        "details": _plain(entry.get("details") or {}),
    }


def _plain(value):
    """Ids and times in details become strings like everywhere else in the API."""
    if isinstance(value, dict):
        return {str(key): _plain(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_plain(item) for item in value]
    if isinstance(value, ObjectId):
        return str(value)
    if isinstance(value, datetime):
        return timestamp(value)
    return value
