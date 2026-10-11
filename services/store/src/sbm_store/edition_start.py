"""Starting due tournament editions (E173–E176); the runner calls this.

The participants are the verified bots with an active registration, seeded by their rating in
the tournament's discipline, ties by lot (E173). The start writes them with the settings and the
first plan in one step; the games follow with edition_games.lay_out, which may repeat.
"""

import random
from datetime import datetime

from bson import ObjectId
from pymongo.database import Database

from sbm_store import (
    bots,
    disciplines,
    edition_games,
    edition_round_robin,
    editions,
    knockout_bracket,
    rating_settings,
    rating_values,
    registrations,
    tournaments,
)
from sbm_store.season_start import LOT_RANGE


def start_due(db: Database, now: datetime, rng: random.Random | None = None) -> list[ObjectId]:
    """Starts each due edition that has enough bots; returns the ids of those started."""
    rng = rng or random.Random()
    started = []
    for edition in editions.due(db, now):
        tournament = tournaments.get(db, edition["tournament_id"])
        if tournament is None or tournament["archived"]:
            continue
        discipline = disciplines.get(db, tournament["discipline_id"])
        if discipline is None:
            continue
        participants = _participants(db, tournament, rng)
        if len(participants) < max(2, tournament["min_participants"]):
            continue
        settings = tournaments.settings(tournament) | {
            "tournament_name": tournament["name"],
            "discipline_snapshot": disciplines.snapshot(discipline).to_document(),
            "tiebreak_discipline_snapshot": _tiebreak_snapshot(db, tournament, discipline),
        }
        plan = _first_plan(tournament, participants)
        running = editions.begin(
            db, edition["_id"], settings=settings, participants=participants, plan=plan, now=now
        )
        if running is not None:
            edition_games.lay_out(db, running, now)
            started.append(running["_id"])
    return started


def _participants(db: Database, tournament: dict, rng: random.Random) -> list[dict]:
    waiting = [
        entry["bot_id"]
        for entry in registrations.active_of_league(
            db, tournament["_id"], target_type=registrations.TOURNAMENT
        )
    ]
    eligible = bots.by_ids(db, waiting, status=bots.VERIFIED)
    start = rating_settings.get(db).start
    entries = [
        {
            "bot_id": bot_id,
            "name": eligible[bot_id]["name"],
            "version": eligible[bot_id].get("version"),
            "rating": rating_values.in_discipline(
                eligible[bot_id], tournament["discipline_id"], start
            )["value"],
            "lot": rng.randrange(LOT_RANGE),
        }
        for bot_id in waiting
        if bot_id in eligible
    ]
    entries.sort(key=lambda entry: (-entry["rating"], entry["lot"]))
    return [entry | {"seed": seed} for seed, entry in enumerate(entries, start=1)]


def _tiebreak_snapshot(db: Database, tournament: dict, discipline: dict) -> dict | None:
    """The discipline of tiebreak and Armageddon games; only knockout has them (E176)."""
    if tournament["format"] != tournaments.KNOCKOUT:
        return None
    chosen = tournament["tiebreak_discipline_id"]
    found = disciplines.get(db, chosen) if chosen is not None else None
    return disciplines.snapshot(found or discipline).to_document()


def _first_plan(tournament: dict, participants: list[dict]) -> dict:
    if tournament["format"] == tournaments.ROUND_ROBIN:
        return edition_round_robin.plan(participants, tournament["games_per_pairing"])
    if tournament["format"] == tournaments.KNOCKOUT:
        bracket_size = knockout_bracket.size(len(participants))
        return {
            "bracket_size": bracket_size,
            "duels": knockout_bracket.first_round(participants, bracket_size),
        }
    # The Swiss system pairs each round once the one before has ended (swiss_rounds).
    return {}
