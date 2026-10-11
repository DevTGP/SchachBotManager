"""Admin: create, change, archive and start leagues; they are never deleted (E131, E132)."""

from flask import Blueprint
from sbm_store import league_setup, leagues

from sbm_api import admin_audit, context, league_request
from sbm_api.current_user import require_admin
from sbm_api.errors import LEAGUE_STATE, NAME_TAKEN, ApiError, not_found
from sbm_api.league_view import league_view
from sbm_api.params import object_id

blueprint = Blueprint("admin_leagues", __name__)


@blueprint.post("/admin/leagues")
def create_league():
    admin = require_admin()
    db = context.db()
    fields = league_request.parse_new(db)
    league = leagues.new_league(fields, created_by=admin["_id"], now=context.now())
    if not league_setup.create(db, league, context.now()):
        raise name_taken()
    admin_audit.record(admin, "league.create", league["_id"], fields)
    return league_view(db, league), 201


@blueprint.patch("/admin/leagues/<league_id>")
def update_league(league_id: str):
    admin = require_admin()
    db = context.db()
    league = _league(league_id)
    fields = league_request.parse_update(db, league)
    try:
        changed = leagues.update(db, league["_id"], fields, now=context.now())
    except leagues.NameTaken:
        raise name_taken() from None
    if changed is None:
        raise not_found("no such league")
    admin_audit.record(admin, "league.update", league["_id"], fields)
    return league_view(db, changed)


@blueprint.post("/admin/leagues/<league_id>/start")
def start_league(league_id: str):
    admin = require_admin()
    db = context.db()
    league = _league(league_id)
    if league["archived"]:
        raise ApiError(409, LEAGUE_STATE, "the league is archived")
    if not league_setup.release(db, league["_id"], context.now()):
        raise ApiError(409, LEAGUE_STATE, "the first season was released already")
    admin_audit.record(admin, "league.start", league["_id"], {"name": league["name"]})
    return league_view(db, league)


def _league(league_id: str) -> dict:
    league = leagues.get(context.db(), object_id(league_id, "league_id"))
    if league is None:
        raise not_found("no such league")
    return league


def name_taken() -> ApiError:
    return ApiError(409, NAME_TAKEN, "another league has the name", "name")
