"""POST /tournaments/{tournament_id}/registrations and DELETE …/registrations/{participant_id}
(E179, E182).

Like registering for a league: the owner (a coder) or an admin registers a verified bot, an
account itself or an admin any active account, and it enters at the next edition start.
Leaving during a running edition withdraws it: its waiting games become forfeits, in knockout
it loses its duel.
"""

from flask import Blueprint
from sbm_store import competition_entrants, registrations, tournament_withdrawal, tournaments

from sbm_api import context, participant_access
from sbm_api.current_user import require_user
from sbm_api.errors import ALREADY_REGISTERED, TOURNAMENT_STATE, ApiError, not_found
from sbm_api.params import object_id
from sbm_api.tournament_view import registration_view

blueprint = Blueprint("tournament_registrations", __name__)
TOURNAMENT = registrations.TOURNAMENT


@blueprint.post("/tournaments/<tournament_id>/registrations")
def register_bot(tournament_id: str):
    user = require_user()
    db = context.db()
    tournament = _tournament(tournament_id)
    holder = participant_access.registrant(user)
    if tournament["archived"]:
        raise ApiError(409, TOURNAMENT_STATE, "the tournament is archived")
    fields = competition_entrants.fields(holder)
    entry = registrations.new_registration(
        tournament["_id"],
        fields["bot_id"],
        user_id=fields["user_id"],
        created_by=user["_id"],
        now=context.now(),
        target_type=TOURNAMENT,
    )
    if not registrations.insert(db, entry):
        field = "user_id" if participant_access.is_account(holder) else "bot_id"
        raise ApiError(409, ALREADY_REGISTERED, "the participant is registered already", field)
    details = {"tournament": tournament["name"]}
    participant_access.audit(user, holder, "tournament.register", details)
    # A participant enters at the next start; it plays in no edition yet.
    return registration_view(entry, tournament, fields, set()), 201


@blueprint.delete("/tournaments/<tournament_id>/registrations/<participant_id>")
def deregister_bot(tournament_id: str, participant_id: str):
    user = require_user()
    db = context.db()
    tournament = _tournament(tournament_id)
    holder = participant_access.managed(user, object_id(participant_id, "participant_id"))
    active = registrations.get_active(db, tournament["_id"], holder["_id"], target_type=TOURNAMENT)
    if active is None:
        raise not_found("the participant is not registered")
    forfeits = tournament_withdrawal.withdraw(
        db,
        holder["_id"],
        registrations.DEREGISTERED,
        context.now(),
        tournament_id=tournament["_id"],
    )
    details = {"tournament": tournament["name"], "forfeits": forfeits}
    participant_access.audit(user, holder, "tournament.deregister", details)
    return "", 204


def _tournament(tournament_id: str) -> dict:
    tournament = tournaments.get(context.db(), object_id(tournament_id, "tournament_id"))
    if tournament is None:
        raise not_found("no such tournament")
    return tournament
