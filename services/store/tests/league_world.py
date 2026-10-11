"""Leagues, bots and results for the store tests of leagues and seasons."""

from bson import ObjectId
from conftest import BLITZ, T0

from sbm_store import bots, disciplines, league_setup, leagues, matches, registrations
from sbm_store.migrate import migrate
from sbm_store.names import MATCHES


def add_bots(db, count: int, *, status: str = bots.VERIFIED) -> list[dict]:
    """count new bots named Bot0, Bot1, … in that order."""
    added = []
    first = db["bots"].count_documents({"name": {"$regex": "^Bot"}})
    for number in range(first, first + count):
        bot = bots.new_uploaded_bot(
            bot_id=ObjectId(),
            name=f"Bot{number}",
            version="1.0",
            language="python",
            entry="bot.py",
            files=[],
            source_hash="",
            owner_id=ObjectId(),
            previous=None,
            now=T0,
        )
        assert bots.insert(db, bot | {"status": status})
        added.append(bots.get(db, bot["_id"]))
    return added


def add_league(db, name: str = "Liga", **settings) -> dict:
    """A migrated database with a new league and its first season, not yet released."""
    migrate(db)
    discipline = disciplines.new_discipline(BLITZ, created_by=None, now=T0)
    if not disciplines.insert(db, discipline):
        discipline = db["disciplines"].find_one({"name_key": "blitz"})
    league = leagues.new_league(
        {"name": name, "discipline_id": discipline["_id"], **settings}, created_by=None, now=T0
    )
    assert league_setup.create(db, league, T0)
    return league


def register(db, league: dict, entrants: list[dict]) -> None:
    for bot in entrants:
        registration = registrations.new_registration(
            league["_id"], bot["_id"], created_by=bot["owner_id"], now=T0
        )
        assert registrations.insert(db, registration)


def season_games(db, season_id: ObjectId, status: str | None = None) -> list[dict]:
    query = matches.match_filter(status=status, season_id=season_id)
    return list(db[MATCHES].find(query).sort("_id", 1))


def play_out(db, season_id: ObjectId, winner_of) -> None:
    """Ends each waiting game of the season; winner_of(white_id, black_id) names the winner or
    None for a draw."""
    for match in season_games(db, season_id, matches.QUEUED):
        white, black = match["white"]["bot_id"], match["black"]["bot_id"]
        winner = winner_of(white, black)
        result = "1/2-1/2" if winner is None else "1-0" if winner == white else "0-1"
        db[MATCHES].update_one(
            {"_id": match["_id"]},
            {"$set": {"status": matches.FINISHED, "result": result, "termination": "checkmate"}},
        )
        db["jobs"].update_one({"payload.match_id": match["_id"]}, {"$set": {"status": "done"}})


def stronger(order: list[dict]):
    """A winner_of where the bot earlier in order always wins."""
    rank = {bot["_id"]: number for number, bot in enumerate(order)}
    return lambda white, black: white if rank[white] < rank[black] else black
