"""The kind and name of the targets on a page of the audit log (U13, E169).

The kind follows from the action; the name is looked up once per kind for the whole page, so it
shows the target as it is now. A deleted bot keeps the name its entry recorded.
"""

from bson import ObjectId
from pymongo.database import Database
from sbm_store.names import BOTS, DISCIPLINES, INVITES, LEAGUES, MATCHES, TOURNAMENTS, USERS

# The first part of an action names the kind of its target; registering in a league or a
# tournament targets a bot.
KINDS = {
    "bot": "bot",
    "match": "match",
    "user": "user",
    "password_reset": "user",
    "discipline": "discipline",
    "league": "league",
    "tournament": "tournament",
    "invite": "invite",
}
BOT_ACTIONS = {
    "league.register",
    "league.deregister",
    "tournament.register",
    "tournament.deregister",
}
COLLECTIONS = {
    "bot": BOTS,
    "match": MATCHES,
    "user": USERS,
    "discipline": DISCIPLINES,
    "league": LEAGUES,
    "tournament": TOURNAMENTS,
    "invite": INVITES,
}
FIELDS = {"bot": ["name"], "match": ["white.name", "black.name"], "user": ["username"]}


def target_kind(entry: dict) -> str | None:
    if entry["target"] is None:
        return None
    action = entry["action"]
    if action in BOT_ACTIONS:
        return "bot"
    return KINDS.get(action.split(".", 1)[0])


def labels(db: Database, entries: list[dict]) -> list[tuple[str | None, str | None]]:
    """(kind, label) for each entry, in order."""
    kinds = [target_kind(entry) for entry in entries]
    wanted: dict[str, set[ObjectId]] = {}
    for kind, entry in zip(kinds, entries, strict=True):
        if kind is not None and isinstance(entry["target"], ObjectId):
            wanted.setdefault(kind, set()).add(entry["target"])
    found = {kind: _names(db, kind, ids) for kind, ids in wanted.items()}
    return [
        (kind, None if kind is None else _label(found.get(kind, {}), entry))
        for kind, entry in zip(kinds, entries, strict=True)
    ]


def _names(db: Database, kind: str, ids: set[ObjectId]) -> dict[ObjectId, str | None]:
    fields = FIELDS.get(kind, ["name"])
    documents = db[COLLECTIONS[kind]].find({"_id": {"$in": list(ids)}}, dict.fromkeys(fields, 1))
    return {document["_id"]: _name(kind, document) for document in documents}


def _name(kind: str, document: dict) -> str | None:
    if kind == "match":
        sides = sorted(
            (document.get(color) or {}).get("name") or "?" for color in ("white", "black")
        )
        return " - ".join(sides)
    if kind == "user":
        return document.get("username")
    return document.get("name")


def _label(found: dict[ObjectId, str | None], entry: dict) -> str | None:
    label = found.get(entry["target"])
    if label is None:
        return (entry.get("details") or {}).get("name")
    return label
