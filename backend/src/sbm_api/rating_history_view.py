"""The rating history of a bot as the API shows it (schema RatingHistory, E140)."""

from bson import ObjectId
from sbm_store.rating_history import Point

from sbm_api.timestamps import timestamp

# A discipline deleted since keeps its games; it has no name any more.
UNKNOWN = "?"


def rating_history_view(history: dict[ObjectId, list[Point]], names: dict) -> dict:
    items = [
        {
            "discipline_id": str(discipline_id),
            "name": names.get(discipline_id, UNKNOWN),
            "games": [_point(point) for point in points],
        }
        for discipline_id, points in history.items()
    ]
    items.sort(key=lambda item: (-len(item["games"]), item["name"]))
    return {"items": items}


def _point(point: Point) -> dict:
    return {
        "match_id": str(point.match_id),
        "finished_at": timestamp(point.finished_at),
        "before": point.before,
        "after": point.after,
    }
