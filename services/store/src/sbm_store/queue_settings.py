"""Queue settings in the settings collection, changeable while the system runs (E13, E20)."""

from dataclasses import dataclass

from pymongo.database import Database

from sbm_store.names import SETTINGS

DOCUMENT_ID = "queue"
DEFAULT_PARALLELISM = 1


@dataclass(frozen=True)
class QueueSettings:
    paused: bool = False
    parallelism: int = DEFAULT_PARALLELISM


def get(db: Database) -> QueueSettings:
    document = db[SETTINGS].find_one({"_id": DOCUMENT_ID}) or {}
    return QueueSettings(
        paused=document.get("paused", False),
        parallelism=document.get("parallelism", DEFAULT_PARALLELISM),
    )


def set_paused(db: Database, paused: bool) -> None:
    db[SETTINGS].update_one({"_id": DOCUMENT_ID}, {"$set": {"paused": paused}}, upsert=True)
