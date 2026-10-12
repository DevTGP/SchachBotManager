"""GET /account/competition-games: the open league and tournament games of the own account, the
released ones first by deadline (E183), with the estimated start of a ready one (E187)."""

from flask import Blueprint
from sbm_store import competition_games, competition_readiness

from sbm_api import context
from sbm_api.current_user import require_user
from sbm_api.match_view import match_summary
from sbm_api.start_estimate import StartEstimate
from sbm_api.timestamps import optional_timestamp

blueprint = Blueprint("account_competition_games", __name__)


@blueprint.get("/account/competition-games")
def competition_games_of_account():
    user = require_user()
    estimate = StartEstimate(context.db(), context.now())
    return {
        "items": [
            {
                "match": match_summary(match),
                "color": competition_readiness.color_of(match, user["_id"]),
                "estimated_start": optional_timestamp(estimate(match)),
            }
            for match in competition_games.of_account(context.db(), user["_id"])
        ]
    }
