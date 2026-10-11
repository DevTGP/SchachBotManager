"""The standings of a started edition (E177): the table of a round robin or Swiss edition, the
placements of a knockout one, and the final result with its winner."""

from pymongo.database import Database

from sbm_store import edition_games, knockout_bracket, league_table, tournaments


def table(db: Database, edition: dict, games: list[dict] | None = None) -> list[league_table.Row]:
    """The rows of a round robin or Swiss edition in their order; games are its matches as
    edition_games.of_edition returns them, read when not given."""
    if games is None:
        games = edition_games.of_edition(db, edition["_id"])
    return league_table.table(
        edition["participants"],
        league_table.counted_games(games),
        points=tournaments.POINTS,
        tiebreaks=edition["settings"]["tiebreaks"],
        withdrawn=edition["withdrawn"],
        byes=byes(edition),
    )


def byes(edition: dict) -> dict:
    """The byes per bot; only those of the Swiss system give a point (E175)."""
    if edition["settings"]["format"] != tournaments.SWISS:
        return {}
    count: dict = {}
    for planned in edition["rounds"]:
        if planned["bye"] is not None:
            count[planned["bye"]] = count.get(planned["bye"], 0) + 1
    return count


def placements(edition: dict) -> list[dict]:
    return knockout_bracket.placements(
        edition["participants"],
        edition["duels"],
        edition["bracket_size"],
        set(edition["withdrawn"]),
    )


def final(db: Database, edition: dict) -> tuple[dict, dict | None]:
    """The final result to store and the winner as {bot_id, name, version}, if there is one."""
    if edition["settings"]["format"] == tournaments.KNOCKOUT:
        places = placements(edition)
        winner = next((each["bot"] for each in places if each["place"] == 1), None)
        return {"placements": places}, winner
    rows = table(db, edition)
    winner = next((row.bot for row in rows if row.rank == 1), None)
    return {"table": [row.to_edition_document() for row in rows]}, winner
