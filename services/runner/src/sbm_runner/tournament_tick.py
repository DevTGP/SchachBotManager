"""The tournament work of each runner round (E174–E179): running editions first, so one that ends
can hand over to the next one in the same round, then the editions that are due."""

import logging
import random
from datetime import datetime

from pymongo.database import Database
from pymongo.errors import PyMongoError
from sbm_store import edition_progress, edition_start

log = logging.getLogger(__name__)


def advance_tournaments(db: Database, now: datetime, rng: random.Random | None = None) -> None:
    """Never stops the runner: a broken edition is logged and tried again next round."""
    try:
        for edition_id in edition_progress.advance_running(db, now, rng):
            log.info("tournaments: edition %s finished", edition_id)
        for edition_id in edition_start.start_due(db, now, rng):
            log.info("tournaments: edition %s started", edition_id)
    except PyMongoError:
        raise
    except Exception:
        log.exception("tournaments: round failed")
