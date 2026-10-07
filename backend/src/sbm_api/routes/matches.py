"""GET /matches, /matches/{match_id} and /matches/{match_id}/pgn."""

from flask import Blueprint, Response, request
from sbm_store import matches

from sbm_api import context
from sbm_api.errors import not_found
from sbm_api.match_view import match_detail, match_summary
from sbm_api.params import integer, object_id, optional_choice, optional_object_id
from sbm_api.pgn import match_pgn

blueprint = Blueprint("matches", __name__)

PGN_MIMETYPE = "application/x-chess-pgn"


@blueprint.get("/matches")
def list_matches():
    args = request.args
    query = matches.match_filter(
        status=optional_choice(args, "status", matches.STATUSES),
        bot_id=optional_object_id(args, "bot_id"),
    )
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
