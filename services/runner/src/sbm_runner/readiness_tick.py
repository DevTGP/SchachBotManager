"""Competition games with an account in each runner round (E183, E184): games past their
deadline end first, then the ready ones start and the next ones are released."""

import logging
from datetime import datetime

from pymongo.database import Database
from pymongo.errors import PyMongoError
from sbm_store import competition_readiness

log = logging.getLogger(__name__)


def advance_readiness(db: Database, now: datetime) -> None:
    """Never stops the runner: a failure is logged and tried again next round."""
    try:
        for match_id in competition_readiness.expire(db, now):
            log.info("readiness: match %s ended, an account was not ready", match_id)
        for match_id in competition_readiness.start_ready(db, now):
            log.info("readiness: match %s started", match_id)
        for match_id in competition_readiness.release(db, now):
            log.info("readiness: match %s released", match_id)
    except PyMongoError:
        raise
    except Exception:
        log.exception("readiness: round failed")
