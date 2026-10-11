"""Tournaments, editions and registrations as the API shows them (schemas Tournament,
TournamentDetail, EditionSummary, TournamentRegistration, E180)."""

from pymongo.database import Database
from sbm_store import disciplines, editions, participants, registrations, tournaments

from sbm_api import recurrence_request
from sbm_api.participant_view import holders, participant
from sbm_api.timestamps import optional_timestamp, timestamp

TOURNAMENT = registrations.TOURNAMENT


def tournament_list(db: Database) -> list[dict]:
    found = tournaments.all_by_name(db)
    names = _discipline_names(db)
    latest = editions.latest_of(db, [tournament["_id"] for tournament in found])
    return [
        tournament_view(db, tournament, names, latest.get(tournament["_id"]))
        for tournament in found
    ]


def tournament_view(
    db: Database, tournament: dict, names: dict | None = None, latest: dict | None = None
) -> dict:
    """names maps discipline ids to names and latest is the newest edition; both are read when
    not given."""
    if names is None:
        names = _discipline_names(db)
        latest = editions.latest(db, tournament["_id"])
    tiebreak_id = tournament["tiebreak_discipline_id"]
    return (
        {
            "id": str(tournament["_id"]),
            "name": tournament["name"],
            "discipline_name": names.get(tournament["discipline_id"], "?"),
        }
        | settings_view(tournaments.settings(tournament))
        | {
            "tiebreak_discipline_name": None
            if tiebreak_id is None
            else names.get(tiebreak_id, "?"),
            "recurrence": recurrence_request.view(tournament.get("recurrence")),
            "archived": tournament["archived"],
            "registered": registrations.count_active(db, tournament["_id"], target_type=TOURNAMENT),
            "edition": None if latest is None else edition_summary(latest),
            "created_at": timestamp(tournament["created_at"]),
            "updated_at": timestamp(tournament["updated_at"]),
        }
    )


def tournament_detail(db: Database, tournament: dict) -> dict:
    found = editions.of_tournament(db, tournament["_id"])
    playing = _playing(found[0] if found else None)
    entries = registrations.active_of_league(db, tournament["_id"], target_type=TOURNAMENT)
    entered = holders(db, entries)
    return tournament_view(db, tournament) | {
        "editions": [edition_summary(edition) for edition in found],
        "registrations": [
            registration_view(entry, tournament, entered[participants.key(entry)], playing)
            for entry in entries
            if participants.key(entry) in entered
        ],
    }


def bot_registrations(db: Database, holder: dict) -> list[dict]:
    """The tournaments a participant is registered for; holder has its entry fields."""
    entries = registrations.active_of_bot(db, participants.key(holder), target_type=TOURNAMENT)
    ids = [entry["target_id"] for entry in entries]
    found = tournaments.by_ids(db, ids)
    latest = editions.latest_of(db, ids)
    return [
        registration_view(
            entry, found[entry["target_id"]], holder, _playing(latest.get(entry["target_id"]))
        )
        for entry in entries
        if entry["target_id"] in found
    ]


def registration_view(entry: dict, tournament: dict, holder: dict, playing: set) -> dict:
    """holder has the participant's entry fields; playing holds the participants of the running
    edition that have not withdrawn."""
    return {
        "tournament_id": str(tournament["_id"]),
        "tournament_name": tournament["name"],
        "bot": participant(holder),
        "created_at": timestamp(entry["created_at"]),
        "playing": participants.key(holder) in playing,
    }


def edition_summary(edition: dict) -> dict:
    winner = edition["winner"]
    return {
        "id": str(edition["_id"]),
        "number": edition["number"],
        "status": edition["status"],
        "starts_after": optional_timestamp(edition["starts_after"]),
        "participants": len(edition["participants"]),
        "winner": None if winner is None else participant(winner),
        "started_at": optional_timestamp(edition["started_at"]),
        "finished_at": optional_timestamp(edition["finished_at"]),
    }


def settings_view(settings: dict) -> dict:
    """The settings of a tournament or the copy an edition keeps, in the order of the schema."""
    tiebreak_id = settings["tiebreak_discipline_id"]
    return {field: settings[field] for field in tournaments.SETTINGS} | {
        "discipline_id": str(settings["discipline_id"]),
        "tiebreak_discipline_id": None if tiebreak_id is None else str(tiebreak_id),
    }


def _playing(edition: dict | None) -> set:
    if edition is None or edition["status"] != editions.RUNNING:
        return set()
    withdrawn = set(edition["withdrawn"])
    return {participants.key(entry) for entry in edition["participants"]} - withdrawn


def _discipline_names(db: Database) -> dict:
    """There are few disciplines; all of them are read at once."""
    return {discipline["_id"]: discipline["name"] for discipline in disciplines.all_by_name(db)}
