"""The results of a bot as the API shows them (schema BotRecord, E141)."""

from bson import ObjectId
from sbm_store.bot_record import Counts

from sbm_api.rating_history_view import UNKNOWN


def bot_record_view(by_discipline: dict[ObjectId | None, Counts], names: dict) -> dict:
    total = sum(by_discipline.values(), Counts())
    disciplines = [
        _discipline(discipline_id, counts, names) for discipline_id, counts in by_discipline.items()
    ]
    disciplines.sort(
        key=lambda item: (item["discipline_id"] is None, -item["games"], item["name"] or "")
    )
    return {"total": _counts(total), "disciplines": disciplines}


def _discipline(discipline_id: ObjectId | None, counts: Counts, names: dict) -> dict:
    if discipline_id is None:
        identity = {"discipline_id": None, "name": None}
    else:
        identity = {"discipline_id": str(discipline_id), "name": names.get(discipline_id, UNKNOWN)}
    return identity | _counts(counts)


def _counts(counts: Counts) -> dict:
    return {
        "games": counts.games,
        "wins": counts.wins,
        "draws": counts.draws,
        "losses": counts.losses,
    }
