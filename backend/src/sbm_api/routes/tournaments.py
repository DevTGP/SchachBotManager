"""GET /tournaments, /tournaments/{tournament_id}, /editions/{edition_id}, …/rounds,
/bots/{bot_id}/tournaments and /bots/{bot_id}/editions (E180)."""

from flask import Blueprint
from sbm_store import bot_editions, bots, competition_entrants, edition_games, editions, tournaments

from sbm_api import context
from sbm_api.bot_access import visible_bot
from sbm_api.bot_edition_view import bot_edition_view
from sbm_api.current_user import current_user
from sbm_api.edition_rounds_view import rounds_view
from sbm_api.edition_view import edition_view
from sbm_api.errors import not_found
from sbm_api.params import object_id
from sbm_api.tournament_view import bot_registrations, tournament_detail, tournament_list

blueprint = Blueprint("tournaments", __name__)


@blueprint.get("/tournaments")
def list_tournaments():
    return {"items": tournament_list(context.db())}


@blueprint.get("/tournaments/<tournament_id>")
def get_tournament(tournament_id: str):
    db = context.db()
    tournament = tournaments.get(db, object_id(tournament_id, "tournament_id"))
    if tournament is None:
        raise not_found("no such tournament")
    return tournament_detail(db, tournament)


@blueprint.get("/editions/<edition_id>")
def get_edition(edition_id: str):
    db = context.db()
    return edition_view(db, _edition(edition_id))


@blueprint.get("/editions/<edition_id>/rounds")
def get_edition_rounds(edition_id: str):
    db = context.db()
    edition = _edition(edition_id)
    return rounds_view(edition, edition_games.of_edition(db, edition["_id"]))


@blueprint.get("/bots/<bot_id>/tournaments")
def get_bot_tournaments(bot_id: str):
    db = context.db()
    bot = visible_bot(bots.get(db, object_id(bot_id, "bot_id")), current_user())
    return {"items": bot_registrations(db, competition_entrants.fields(bot))}


@blueprint.get("/bots/<bot_id>/editions")
def get_bot_editions(bot_id: str):
    db = context.db()
    bot = visible_bot(bots.get(db, object_id(bot_id, "bot_id")), current_user())
    return {
        "items": [
            bot_edition_view(found, bot["_id"]) for found in bot_editions.of_bot(db, bot["_id"])
        ]
    }


def _edition(edition_id: str) -> dict:
    edition = editions.get(context.db(), object_id(edition_id, "edition_id"))
    if edition is None:
        raise not_found("no such edition")
    return edition
