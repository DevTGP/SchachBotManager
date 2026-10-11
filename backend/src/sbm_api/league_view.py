"""Leagues, seasons and registrations as the API shows them (schemas League, LeagueDetail,
SeasonSummary, LeagueRegistration, E137)."""

from pymongo.database import Database
from sbm_store import bots, disciplines, leagues, registrations, seasons

from sbm_api.timestamps import optional_timestamp, timestamp


def league_list(db: Database) -> list[dict]:
    found = leagues.all_by_name(db)
    names = _discipline_names(db)
    return [league_view(db, league, names.get(league["discipline_id"], "?")) for league in found]


def league_view(db: Database, league: dict, discipline_name: str | None = None) -> dict:
    if discipline_name is None:
        discipline_name = _discipline_names(db).get(league["discipline_id"], "?")
    latest = seasons.latest(db, league["_id"])
    settings = settings_view(leagues.settings(league))
    return (
        {"id": str(league["_id"]), "name": league["name"], "discipline_name": discipline_name}
        | settings
        | {
            "archived": league["archived"],
            "registered": registrations.count_active(db, league["_id"]),
            "season": None if latest is None else season_summary(latest),
            "created_at": timestamp(league["created_at"]),
            "updated_at": timestamp(league["updated_at"]),
        }
    )


def league_detail(db: Database, league: dict) -> dict:
    running = _running(db, league["_id"])
    entries = registrations.active_of_league(db, league["_id"])
    found = bots.by_ids(db, [entry["bot_id"] for entry in entries])
    return league_view(db, league) | {
        "seasons": [season_summary(season) for season in seasons.of_league(db, league["_id"])],
        "registrations": [
            registration_view(entry, league, found[entry["bot_id"]], running)
            for entry in entries
            if entry["bot_id"] in found
        ],
    }


def bot_registrations(db: Database, bot: dict) -> list[dict]:
    entries = registrations.active_of_bot(db, bot["_id"])
    found = leagues.by_ids(db, [entry["target_id"] for entry in entries])
    return [
        registration_view(entry, found[entry["target_id"]], bot, _running(db, entry["target_id"]))
        for entry in entries
        if entry["target_id"] in found
    ]


def registration_view(entry: dict, league: dict, bot: dict, running: dict | None) -> dict:
    """running is the league's running season, if any: the tier is the bot's tier there."""
    return {
        "league_id": str(league["_id"]),
        "league_name": league["name"],
        "bot": league_bot({"bot_id": bot["_id"], "name": bot["name"], "version": bot["version"]}),
        "created_at": timestamp(entry["created_at"]),
        "tier": None if running is None else seasons.tier_of(running, bot["_id"]),
    }


def season_summary(season: dict) -> dict:
    return {
        "id": str(season["_id"]),
        "number": season["number"],
        "status": season["status"],
        "starts_after": optional_timestamp(season["starts_after"]),
        "participants": sum(len(tier["entries"]) for tier in season["tiers"]),
        "started_at": optional_timestamp(season["started_at"]),
        "finished_at": optional_timestamp(season["finished_at"]),
    }


def settings_view(settings: dict) -> dict:
    """The settings of a league or the copy a season keeps, in the order of the schema."""
    return {field: settings[field] for field in leagues.SETTINGS} | {
        "discipline_id": str(settings["discipline_id"])
    }


def league_bot(bot: dict) -> dict:
    """A bot as the season or registration knows it (schema LeagueBot)."""
    return {"bot_id": str(bot["bot_id"]), "name": bot["name"], "version": bot.get("version")}


def _running(db: Database, league_id) -> dict | None:
    latest = seasons.latest(db, league_id)
    return latest if latest is not None and latest["status"] == seasons.RUNNING else None


def _discipline_names(db: Database) -> dict:
    """There are few disciplines; all of them are read at once."""
    return {discipline["_id"]: discipline["name"] for discipline in disciplines.all_by_name(db)}
