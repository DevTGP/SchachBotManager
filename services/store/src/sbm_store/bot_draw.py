"""Drawing a random opponent among the verified bots (E162)."""

from bson import ObjectId
from pymongo.database import Database

from sbm_store.bots import VERIFIED
from sbm_store.names import BOTS


def candidates(db: Database, exclude: list[ObjectId]) -> int:
    """How many verified bots a draw that leaves out exclude can give."""
    return db[BOTS].count_documents({"status": VERIFIED, "_id": {"$nin": exclude}})


def draw(db: Database, exclude: list[ObjectId]) -> dict | None:
    """One verified bot not in exclude, every one equally likely; None if there is none."""
    match = {"status": VERIFIED, "_id": {"$nin": exclude}}
    pipeline = [{"$match": match}, {"$sample": {"size": 1}}]
    return next(db[BOTS].aggregate(pipeline), None)
