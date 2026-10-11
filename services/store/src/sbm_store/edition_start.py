"""Starting due tournament editions (E173–E176); the runner calls this.

The participants are the verified bots and active accounts with an active registration, seeded
by their rating in the tournament's discipline, ties by lot (E173, E182). The start writes them
with the settings and the first plan in one step; the games follow with edition_games.lay_out,
which may repeat.
"""

import random
from datetime import datetime

from bson import ObjectId
from pymongo.database import Database

from sbm_store import (
    competition_entrants,
    disciplines,
    edition_games,
    edition_round_robin,
    editions,
    knockout_bracket,
    participants,
    rating_settings,
    rating_values,
    registrations,
    tournaments,
)
from sbm_store.season_start import LOT_RANGE


def start_due(db: Database, now: datetime, rng: random.Random | None = None) -> list[ObjectId]:
    """Starts each due edition that has enough participants; returns the ids of those started."""
    rng = rng or random.Random()
    started = []
    for edition in editions.due(db, now):
        tournament = tournaments.get(db, edition["tournament_id"])
        if tournament is None or tournament["archived"]:
            continue
        discipline = disciplines.get(db, tournament["discipline_id"])
        if discipline is None:
            continue
        entries = _participants(db, tournament, rng)
        if len(entries) < max(2, tournament["min_participants"]):
            continue
        settings = tournaments.settings(tournament) | {
            "tournament_name": tournament["name"],
            "discipline_snapshot": disciplines.snapshot(discipline).to_document(),
            "tiebreak_discipline_snapshot": _tiebreak_snapshot(db, tournament, discipline),
        }
        plan = _first_plan(tournament, entries)
        running = editions.begin(
            db, edition["_id"], settings=settings, participants=entries, plan=plan, now=now
        )
        if running is not None:
            edition_games.lay_out(db, running, now)
            started.append(running["_id"])
    return started


def _participants(db: Database, tournament: dict, rng: random.Random) -> list[dict]:
    registered = registrations.active_of_league(
        db, tournament["_id"], target_type=registrations.TOURNAMENT
    )
    eligible = competition_entrants.holders(db, registered)
    start = rating_settings.get(db).start
    entries = [
        competition_entrants.fields(eligible[key])
        | {
            "rating": rating_values.in_discipline(
                eligible[key], tournament["discipline_id"], start
            )["value"],
            "lot": rng.randrange(LOT_RANGE),
        }
        for key in (participants.key(entry) for entry in registered)
        if key in eligible
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


def _first_plan(tournament: dict, entries: list[dict]) -> dict:
    if tournament["format"] == tournaments.ROUND_ROBIN:
        return edition_round_robin.plan(entries, tournament["games_per_pairing"])
    if tournament["format"] == tournaments.KNOCKOUT:
        bracket_size = knockout_bracket.size(len(entries))
        return {
            "bracket_size": bracket_size,
            "duels": knockout_bracket.first_round(entries, bracket_size),
        }
    # The Swiss system pairs each round once the one before has ended (swiss_rounds).
    return {}
