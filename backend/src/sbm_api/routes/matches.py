"""GET /matches, /matches/{match_id} and /matches/{match_id}/pgn."""

from flask import Blueprint, Response, request
from sbm_store import matches, play

from sbm_api import context
from sbm_api.current_user import require_user
from sbm_api.errors import invalid_parameter, not_found
from sbm_api.match_view import match_detail, match_summary
from sbm_api.params import integer, object_id, optional_choice, optional_object_id
from sbm_api.pgn import match_pgn

blueprint = Blueprint("matches", __name__)

PGN_MIMETYPE = "application/x-chess-pgn"
# Games of people and remote bots are public like those of bots and can be filtered (E119).
KINDS = {
    "bots": {"type": "single"},
    "players": {"type": {"$in": list(play.MATCH_TYPES)}},
}


@blueprint.get("/matches")
def list_matches():
    args = request.args
    bot_id = optional_object_id(args, "bot_id")
    opponent_id = optional_object_id(args, "opponent_id")
    if opponent_id is not None and bot_id is None:
        raise invalid_parameter("opponent_id", "opponent_id needs bot_id")
    # Who set a match stays internal; an account sees only its own (E156).
    mine = optional_choice(args, "mine", ("true", "false")) == "true"
    query = matches.match_filter(
        status=optional_choice(args, "status", matches.STATUSES),
        bot_id=bot_id,
        opponent_id=opponent_id,
        discipline_id=optional_object_id(args, "discipline_id"),
        created_by=require_user()["_id"] if mine else None,
    )
    kind = optional_choice(args, "kind", tuple(KINDS))
    if kind is not None:
        query |= KINDS[kind]
    items, total = matches.page(
        context.db(),
        query,
        limit=integer(args, "limit", default=20, low=1, high=100),
        offset=integer(args, "offset", default=0, low=0, high=1_000_000),
    )
    return {"items": [match_summary(match) for match in items], "total": total}


@blueprint.get("/matches/<match_id>")
def get_match(match_id: str):
    return match_detail(_match(match_id))


@blueprint.get("/matches/<match_id>/pgn")
def get_match_pgn(match_id: str):
    match = _match(match_id)
    return Response(
        match_pgn(match, context.public_url()),
        mimetype=PGN_MIMETYPE,
        headers={"Content-Disposition": f'attachment; filename="match-{match_id}.pgn"'},
    )


def _match(match_id: str) -> dict:
    match = matches.get(context.db(), object_id(match_id, "match_id"))
    if match is None:
        raise not_found("no such match")
    return match
