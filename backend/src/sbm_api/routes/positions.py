"""POST /positions/from-pgn: a start position from a recorded game (E159).

A pure computation with the core through sbm.arena.replay, as sbm-arena --replay does (E69);
nothing is stored and no process starts.
"""

from flask import Blueprint
from sbm.arena.pgn_reader import PgnError, read_games
from sbm.arena.replay import ReplayError, replay_fen

from sbm_api import body
from sbm_api.current_user import require_coder
from sbm_api.errors import invalid_parameter

blueprint = Blueprint("positions", __name__)

MAX_PGN = 65536
FIELDS = ("pgn", "game", "plies")


@blueprint.post("/positions/from-pgn")
def position_from_pgn():
    require_coder()
    data = body.json_object(FIELDS)
    pgn = body.string(data, "pgn", max_length=MAX_PGN)
    number = body.integer(data, "game", low=1, high=1_000_000, default=1)
    plies = data.get("plies")
    if plies is not None:
        plies = body.integer(data, "plies", low=0, high=1_000_000)
    try:
        games = read_games(pgn)
    except PgnError as error:
        raise invalid_parameter("pgn", str(error)) from error
    # Checked here as well, so the error names the field to change.
    if number > len(games):
        raise invalid_parameter("game", f"there is no game {number}, the PGN has {len(games)}")
    if plies is not None and plies > len(games[number - 1].moves):
        raise invalid_parameter("plies", f"game {number} has fewer half-moves")
    try:
        return {"fen": replay_fen(pgn, number, plies)}
    except ReplayError as error:
        raise invalid_parameter("pgn", str(error)) from error
