"""Plays the match of a claimed job and stores the result."""

import logging
from collections.abc import Callable
from datetime import datetime

from pymongo.database import Database
from sbm.referee import Match, MatchRecord, Player
from sbm_store import bots, jobs, matches

from sbm_runner.match_settings import match_settings
from sbm_runner.players import PlayerFactory, UnsupportedBot
from sbm_runner.recorder import Recorder

log = logging.getLogger(__name__)

COLORS = ("white", "black")


def run_job(
    db: Database, job: dict, *, players: PlayerFactory, now: Callable[[], datetime]
) -> None:
    """Exceptions are infrastructure errors; the caller retries or aborts the match."""
    match_id = job["payload"]["match_id"]
    match = matches.get(db, match_id)
    if match is None:
        log.error("job %s refers to the missing match %s", job["_id"], match_id)
        jobs.fail(db, job["_id"], now())
        return
    if match["status"] in (matches.FINISHED, matches.ABORTED):
        # The previous worker stored the result but died before closing the job.
        jobs.complete(db, job["_id"], job["worker_id"], now())
        return
    if match["status"] == matches.RUNNING:
        log.warning("match %s was left running by a dead worker, starting over", match_id)
        matches.requeue(db, match_id)

    try:
        white, black = (bot_player(db, match[color], players) for color in COLORS)
    except UnsupportedBot as error:
        log.error("match %s cannot be played: %s", match_id, error)
        matches.abort(db, match_id, str(error), now())
        jobs.fail(db, job["_id"], now())
        return

    if not matches.start(db, match_id, now()):
        log.warning("match %s changed while it was being prepared, not playing it", match_id)
        jobs.complete(db, job["_id"], job["worker_id"], now())
        return
    log.info("match %s: %s vs %s", match_id, white.name, black.name)
    record = Match(
        white, black, match_settings(match), on_move=Recorder(db, match_id).on_move
    ).play()
    store_result(db, match_id, record, now())
    jobs.complete(db, job["_id"], job["worker_id"], now())
    log.info("match %s: %s (%s)", match_id, record.outcome.result, record.outcome.termination)


def bot_player(db: Database, side: dict, players: PlayerFactory) -> Player:
    bot = bots.get(db, side["bot_id"])
    if bot is None:
        raise UnsupportedBot(f"bot {side['bot_id']} does not exist")
    if bot["status"] != bots.VERIFIED:
        # Disabled or retired after the match was queued, or never verified (E93, E96).
        raise UnsupportedBot(f"bot {bot['name']} {bot.get('version', '')} is {bot['status']}")
    return players(bot)


def store_result(db: Database, match_id, record: MatchRecord, now: datetime) -> None:
    outcome = record.outcome
    sides = {
        color: {"sdk": side.sdk, "lang": side.lang}
        for color, side in zip(COLORS, (record.white, record.black), strict=True)
    }
    matches.finish(
        db,
        match_id,
        sides=sides,
        result=outcome.result,
        termination=outcome.termination,
        detail=outcome.detail,
        now=now,
    )
