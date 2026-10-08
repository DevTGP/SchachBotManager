"""Limits of interactive games in the settings collection, changeable on the website (E13, E115).

max_games is the number the play runner holds at once; games_per_client and games_per_day apply
to each address, account and API token on its own.
"""

from dataclasses import asdict, dataclass

from pymongo.database import Database

from sbm_store.names import SETTINGS

DOCUMENT_ID = "play"
# Inclusive ranges the web API accepts.
LIMITS = {"max_games": (1, 16), "games_per_client": (1, 4), "games_per_day": (1, 1000)}


@dataclass(frozen=True)
class PlaySettings:
    max_games: int = 2
    games_per_client: int = 1
    games_per_day: int = 50

    def to_document(self) -> dict:
        return asdict(self)


def get(db: Database) -> PlaySettings:
    document = db[SETTINGS].find_one({"_id": DOCUMENT_ID}) or {}
    defaults = PlaySettings()
    return PlaySettings(**{name: document.get(name, getattr(defaults, name)) for name in LIMITS})


def save(db: Database, settings: PlaySettings) -> None:
    db[SETTINGS].update_one({"_id": DOCUMENT_ID}, {"$set": settings.to_document()}, upsert=True)
