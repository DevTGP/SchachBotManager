"""Renews the lease of a job in the background while the worker plays it."""

import logging
import threading
from collections.abc import Callable
from datetime import datetime, timedelta

from bson import ObjectId
from pymongo.database import Database
from pymongo.errors import PyMongoError
from sbm_store import jobs

log = logging.getLogger(__name__)


class Heartbeat:
    """Use as a context manager around the work on one job."""

    def __init__(
        self,
        db: Database,
        job_id: ObjectId,
        worker_id: str,
        *,
        lease: timedelta,
        interval: timedelta,
        now: Callable[[], datetime],
    ) -> None:
        self._db = db
        self._job_id = job_id
        self._worker_id = worker_id
        self._lease = lease
        self._interval = interval
        self._now = now
        self._stopped = threading.Event()
        self._thread = threading.Thread(target=self._run, name="heartbeat", daemon=True)

    def __enter__(self) -> "Heartbeat":
        self._thread.start()
        return self

    def __exit__(self, *exc_info) -> None:
        self._stopped.set()
        self._thread.join()

    def _run(self) -> None:
        while not self._stopped.wait(self._interval.total_seconds()):
            try:
                held = jobs.extend(
                    self._db, self._job_id, self._worker_id, self._now() + self._lease
                )
            except PyMongoError as error:
                # The next beat tries again; the lease outlasts a few failed ones.
                log.warning("cannot renew the lease of job %s: %s", self._job_id, error)
                continue
            if not held:
                log.error("job %s is no longer held by %s", self._job_id, self._worker_id)
                return
