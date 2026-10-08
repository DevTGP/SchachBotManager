"""Timing and retry settings of the runner."""

import os
import socket
from dataclasses import dataclass
from datetime import timedelta


@dataclass(frozen=True)
class RunnerConfig:
    """lease must outlast several heartbeats, so a slow database write does not lose the job.

    max_attempts and retry_delay apply to matches and verifications alike.
    """

    worker_id: str
    poll_interval: timedelta = timedelta(seconds=2)
    lease: timedelta = timedelta(seconds=60)
    heartbeat: timedelta = timedelta(seconds=15)
    # A match that fails this often for infrastructure reasons is aborted.
    max_attempts: int = 3
    retry_delay: timedelta = timedelta(seconds=30)
    # A verification that waited this long goes ahead of the next match (E89).
    verification_wait: timedelta = timedelta(minutes=15)


def default_worker_id() -> str:
    return f"{socket.gethostname()}-{os.getpid()}"
