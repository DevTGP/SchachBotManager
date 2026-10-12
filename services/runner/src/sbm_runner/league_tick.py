"""The league work of each runner round (E132–E136): schedules, withdrawals, the jobs of the next
rounds (E187), season ends and starts, in this order, so a season that ends can hand over to the
next one in the same round."""

import logging
import random
from datetime import datetime

from pymongo.database import Database
from pymongo.errors import PyMongoError
from sbm_store import league_withdrawal, season_end, season_start

log = logging.getLogger(__name__)


def advance_leagues(db: Database, now: datetime, rng: random.Random | None = None) -> None:
    """Never stops the runner: a broken league is logged and tried again next round."""
    try:
        if season_start.lay_out_pending(db, now):
            log.info("leagues: laid out the schedule of a started season again")
        forfeited = league_withdrawal.sweep(db, now)
        if forfeited:
            log.info("leagues: %d game(s) forfeited by withdrawn bots", forfeited)
        added = season_start.hand_out(db, now)
        if added:
            log.info("leagues: %d game(s) of the next round queued", added)
        for season_id in season_end.finish_done(db, now):
            log.info("leagues: season %s finished", season_id)
        for season_id in season_start.start_due(db, now, rng):
            log.info("leagues: season %s started", season_id)
    except PyMongoError:
        raise
    except Exception:
        log.exception("leagues: round failed")
