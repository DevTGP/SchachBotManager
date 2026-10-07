"""The reference bots of the SDK as bots on the server (E68, E72)."""

from datetime import UTC, datetime

from bson import ObjectId
from pymongo.database import Database

from sbm_store import bots
from sbm_store.names import BOTS

REFERENCE_BOTS = [("Random", "random_mover"), ("Material", "material")]


def apply(db: Database) -> None:
    now = datetime.now(UTC)
    for name, module in REFERENCE_BOTS:
        bot_id = ObjectId()
        db[BOTS].update_one(
            {"source_ref": bots.BUILTIN_PREFIX + module},
            {
                "$setOnInsert": {
                    "_id": bot_id,
                    "schema_version": bots.SCHEMA_VERSION,
                    "name": name,
                    "language": "python",
                    "owner_id": None,
                    "lineage_id": bot_id,
                    "parent_bot_id": None,
                    "version_no": 1,
                    "status": bots.VERIFIED,
                    "created_at": now,
                }
            },
            upsert=True,
        )
