"""Admin: read the audit log with filters (E85, E151)."""

from datetime import UTC, date, datetime, time, timedelta

from bson import ObjectId
from flask import Blueprint, request
from sbm_store import audit

from sbm_api import context
from sbm_api.audit_view import audit_view
from sbm_api.current_user import require_admin
from sbm_api.errors import invalid_parameter
from sbm_api.params import OBJECT_ID, integer, optional_date

blueprint = Blueprint("admin_audit_log", __name__)

MAX_TEXT = 64


@blueprint.get("/admin/audit")
def list_audit_entries():
    require_admin()
    args = request.args
    since, until = optional_date(args, "since"), optional_date(args, "until")
    query = audit.entry_filter(
        actor=_text(args, "actor"),
        action=_text(args, "action"),
        target=_target(_text(args, "target")),
        since=None if since is None else _start_of(since),
        before=None if until is None or until == date.max else _start_of(until + timedelta(days=1)),
    )
    db = context.db()
    items, total = audit.page(
        db,
        query,
        limit=integer(args, "limit", default=20, low=1, high=100),
        offset=integer(args, "offset", default=0, low=0, high=1_000_000),
    )
    return {
        "items": [audit_view(entry) for entry in items],
        "total": total,
        "actions": audit.actions(db),
        "actors": audit.actors(db),
    }


def _text(args, field: str) -> str | None:
    value = args.get(field)
    if value is not None and not 1 <= len(value) <= MAX_TEXT:
        raise invalid_parameter(field, f"{field} must have 1 to {MAX_TEXT} characters")
    return value


def _target(value: str | None) -> ObjectId | str | None:
    """Targets are stored as ids where they are ids."""
    if value is not None and OBJECT_ID.fullmatch(value):
        return ObjectId(value)
    return value


def _start_of(day: date) -> datetime:
    return datetime.combine(day, time(), tzinfo=UTC)
