"""Admin: interventions in single games of the queue – priority, cancel, repeat (E152)."""

from bson import ObjectId
from flask import Blueprint
from pymongo.database import Database
from sbm_store import bots, disciplines, jobs, matches
from sbm_store.discipline import Discipline
from sbm_store.enqueue import DEFAULT_PRIORITY, enqueue_match

from sbm_api import admin_audit, body, context
from sbm_api.current_user import require_admin
from sbm_api.errors import MATCH_STATE, NOT_REPEATABLE, ApiError, not_found
from sbm_api.params import object_id

blueprint = Blueprint("admin_match_actions", __name__)

SINGLE = "single"
MAX_PRIORITY = 1000
CANCEL_DETAIL = "cancelled by an admin"


@blueprint.patch("/admin/matches/<match_id>")
def update_match_priority(match_id: str):
    admin = require_admin()
    db = context.db()
    match = _single_match(db, match_id)
    priority = body.integer(body.json_object(("priority",)), "priority", low=0, high=MAX_PRIORITY)
    if match["status"] != matches.QUEUED or not jobs.set_match_priority(db, match["_id"], priority):
        raise _state_error("only a waiting match can change its priority")
    matches.set_priority(db, match["_id"], priority)
    before = (match.get("queue") or {}).get("priority")
    admin_audit.record(
        admin, "match.priority", match["_id"], {"priority": priority, "before": before}
    )
    return {"priority": priority}


@blueprint.post("/admin/matches/<match_id>/cancel")
def cancel_match(match_id: str):
    admin = require_admin()
    db, now = context.db(), context.now()
    match = _single_match(db, match_id)
    if match["status"] not in (matches.QUEUED, matches.RUNNING):
        raise _state_error("the match has ended already")
    # The job goes first: a runner that holds it loses it and stops the bots.
    jobs.cancel_match(db, match["_id"], now)
    if not matches.abort(db, match["_id"], CANCEL_DETAIL, now):
        raise _state_error("the match has ended already")
    admin_audit.record(admin, "match.cancel", match["_id"], {"status": match["status"]})
    return "", 204


@blueprint.post("/admin/matches/<match_id>/repeat")
def repeat_match(match_id: str):
    admin = require_admin()
    db, now = context.db(), context.now()
    match = _single_match(db, match_id)
    if match["status"] not in (matches.FINISHED, matches.ABORTED):
        raise _state_error("only an ended match can be repeated")
    white = _verified_bot(db, match["white"])
    black = _verified_bot(db, match["black"])
    discipline = _current_discipline(db, match["discipline_snapshot"])
    priority = (match.get("queue") or {}).get("priority", DEFAULT_PRIORITY)
    # The wish for an unrated game carries over (E158); the repeat is the admin's match (E156).
    new_id = enqueue_match(
        db,
        white,
        black,
        discipline,
        start_fen=match["start_fen"],
        now=now,
        priority=priority,
        rated=match.get("rated", False),
        created_by=admin["_id"],
    )
    admin_audit.record(admin, "match.repeat", new_id, {"from": str(match["_id"])})
    return {"match_ids": [str(new_id)], "series_id": None}, 201


def _single_match(db: Database, match_id: str) -> dict:
    match = matches.get(db, object_id(match_id, "match_id"))
    if match is None:
        raise not_found("no such match")
    if match["type"] != SINGLE:
        raise _state_error("only single games can be changed here")
    return match


def _verified_bot(db: Database, side: dict) -> dict:
    bot_id = side.get("bot_id")
    bot = bots.get(db, bot_id) if isinstance(bot_id, ObjectId) else None
    if bot is None or bot["status"] != bots.VERIFIED:
        raise ApiError(409, NOT_REPEATABLE, f"{side['name']} is not a verified bot any more")
    return bot


def _current_discipline(db: Database, snapshot: dict) -> Discipline:
    """The discipline as it is now; free times from before E100 are kept as they were."""
    discipline_id = snapshot.get("discipline_id")
    if discipline_id is None:
        return Discipline.from_document(snapshot)
    discipline = disciplines.get(db, discipline_id)
    if discipline is None or discipline["archived"]:
        raise ApiError(409, NOT_REPEATABLE, "the discipline is archived")
    return disciplines.snapshot(discipline)


def _state_error(message: str) -> ApiError:
    return ApiError(409, MATCH_STATE, message)
