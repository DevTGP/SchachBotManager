"""POST /leagues/{league_id}/registrations and DELETE …/registrations/{participant_id} (E136,
E182).

The owner (a coder) or an admin registers a verified bot; an account registers itself, an
admin any active account. The participant enters at the next season start. Leaving during a
running season withdraws it: its waiting games become forfeits.
"""

from flask import Blueprint
from sbm_store import competition_entrants, league_withdrawal, leagues, registrations

from sbm_api import context, participant_access
from sbm_api.current_user import require_user
from sbm_api.errors import ALREADY_REGISTERED, LEAGUE_STATE, ApiError, not_found
from sbm_api.league_view import registration_view
from sbm_api.params import object_id

blueprint = Blueprint("league_registrations", __name__)


@blueprint.post("/leagues/<league_id>/registrations")
def register_bot(league_id: str):
    user = require_user()
    db = context.db()
    league = _league(league_id)
    holder = participant_access.registrant(user)
    if league["archived"]:
        raise ApiError(409, LEAGUE_STATE, "the league is archived")
    fields = competition_entrants.fields(holder)
    entry = registrations.new_registration(
        league["_id"],
        fields["bot_id"],
        user_id=fields["user_id"],
        created_by=user["_id"],
        now=context.now(),
    )
    if not registrations.insert(db, entry):
        field = "user_id" if participant_access.is_account(holder) else "bot_id"
        raise ApiError(409, ALREADY_REGISTERED, "the participant is registered already", field)
    participant_access.audit(user, holder, "league.register", {"league": league["name"]})
    # A participant enters at the next start; it has no tier yet.
    return registration_view(entry, league, fields, None), 201


@blueprint.delete("/leagues/<league_id>/registrations/<participant_id>")
def deregister_bot(league_id: str, participant_id: str):
    user = require_user()
    db = context.db()
    league = _league(league_id)
    holder = participant_access.managed(user, object_id(participant_id, "participant_id"))
    if registrations.get_active(db, league["_id"], holder["_id"]) is None:
        raise not_found("the participant is not registered")
    forfeits = league_withdrawal.withdraw(
        db, holder["_id"], registrations.DEREGISTERED, context.now(), league_id=league["_id"]
    )
    details = {"league": league["name"], "forfeits": forfeits}
    participant_access.audit(user, holder, "league.deregister", details)
    return "", 204


def _league(league_id: str) -> dict:
    league = leagues.get(context.db(), object_id(league_id, "league_id"))
    if league is None:
        raise not_found("no such league")
    return league
