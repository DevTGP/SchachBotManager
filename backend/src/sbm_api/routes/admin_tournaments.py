"""Admin: create, change, archive and start tournaments; they are never deleted (E172)."""

from flask import Blueprint
from sbm_store import tournament_setup, tournaments

from sbm_api import admin_audit, context, tournament_request
from sbm_api.current_user import require_admin
from sbm_api.errors import NAME_TAKEN, TOURNAMENT_STATE, ApiError, not_found
from sbm_api.params import object_id
from sbm_api.tournament_view import tournament_view

blueprint = Blueprint("admin_tournaments", __name__)


@blueprint.post("/admin/tournaments")
def create_tournament():
    admin = require_admin()
    db = context.db()
    fields = tournament_request.parse_new(db)
    tournament = tournaments.new_tournament(fields, created_by=admin["_id"], now=context.now())
    if not tournament_setup.create(db, tournament, context.now()):
        raise name_taken()
    admin_audit.record(admin, "tournament.create", tournament["_id"], fields)
    return tournament_view(db, tournament), 201


@blueprint.patch("/admin/tournaments/<tournament_id>")
def update_tournament(tournament_id: str):
    admin = require_admin()
    db = context.db()
    tournament = _tournament(tournament_id)
    fields = tournament_request.parse_update(db)
    try:
        changed = tournaments.update(db, tournament["_id"], fields, now=context.now())
    except tournaments.NameTaken:
        raise name_taken() from None
    if changed is None:
        raise not_found("no such tournament")
    if "recurrence" in fields:
        tournament_setup.follow_calendar(db, changed, context.now())
    admin_audit.record(admin, "tournament.update", tournament["_id"], fields)
    return tournament_view(db, changed)


@blueprint.post("/admin/tournaments/<tournament_id>/start")
def start_tournament(tournament_id: str):
    admin = require_admin()
    db = context.db()
    tournament = _tournament(tournament_id)
    if tournament["archived"]:
        raise ApiError(409, TOURNAMENT_STATE, "the tournament is archived")
    if not tournament_setup.start(db, tournament["_id"], context.now()):
        raise ApiError(409, TOURNAMENT_STATE, "no planned edition waits or it is due already")
    admin_audit.record(admin, "tournament.start", tournament["_id"], {"name": tournament["name"]})
    return tournament_view(db, tournament)


def _tournament(tournament_id: str) -> dict:
    tournament = tournaments.get(context.db(), object_id(tournament_id, "tournament_id"))
    if tournament is None:
        raise not_found("no such tournament")
    return tournament


def name_taken() -> ApiError:
    return ApiError(409, NAME_TAKEN, "another tournament has the name", "name")
