"""Runs the pending migrations; the migrate service does this before the others start."""

import logging
import sys
from datetime import UTC, datetime

from pymongo.database import Database

from sbm_store.connection import database_from_env
from sbm_store.migrations import MIGRATIONS
from sbm_store.names import MIGRATIONS as MIGRATIONS_COLLECTION

log = logging.getLogger(__name__)


def migrate(db: Database, migrations=MIGRATIONS) -> list[str]:
    """Applies each migration not yet recorded, in order; returns the ids applied now.

    Runs from one process at a time. A migration that fails stays unrecorded and runs again
    next time, so each one must be safe to repeat.
    """
    done = {record["_id"] for record in db[MIGRATIONS_COLLECTION].find({}, {"_id": 1})}
    applied = []
    for migration_id, apply in migrations:
        if migration_id in done:
            continue
        log.info("applying migration %s", migration_id)
        apply(db)
        db[MIGRATIONS_COLLECTION].insert_one({"_id": migration_id, "applied_at": datetime.now(UTC)})
        applied.append(migration_id)
    return applied


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    applied = migrate(database_from_env())
    log.info("%d migration(s) applied", len(applied))
    return 0


if __name__ == "__main__":
    sys.exit(main())
