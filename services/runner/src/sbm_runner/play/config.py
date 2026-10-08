"""Settings of the play runner, from the environment as in the container."""

import os
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import timedelta

from sbm_runner.config import default_worker_id


@dataclass(frozen=True)
class PlayConfig:
    """slots: interactive games at the same time. connect_wait: time for each person or remote
    bot to take its seat before the game starts. absent_grace: time a client may be away
    during the game before it is aborted (E113).
    """

    worker_id: str = field(default_factory=default_worker_id)
    relay_host: str = "127.0.0.1"
    relay_port: int = 9000
    slots: int = 2
    poll_interval: timedelta = timedelta(seconds=1)
    lease: timedelta = timedelta(seconds=60)
    heartbeat: timedelta = timedelta(seconds=15)
    connect_wait: timedelta = timedelta(seconds=30)
    absent_grace: timedelta = timedelta(seconds=60)
    # Time to reach the gateway at all.
    relay_timeout: timedelta = timedelta(seconds=5)
    # On shutdown, running games get this long to notice that their seats are gone.
    stop_wait: timedelta = timedelta(seconds=15)

    @property
    def relay_address(self) -> tuple[str, int]:
        return self.relay_host, self.relay_port

    @classmethod
    def from_env(cls, environ: Mapping[str, str] = os.environ) -> "PlayConfig":
        defaults = cls(worker_id=environ.get("SBM_WORKER_ID") or default_worker_id())
        address = environ.get("SBM_RELAY_ADDRESS")
        host, port = defaults.relay_host, defaults.relay_port
        if address:
            host, _, port_text = address.rpartition(":")
            if not host or not port_text.isdigit() or not 1 <= int(port_text) <= 65535:
                raise ValueError(f"SBM_RELAY_ADDRESS must be host:port, not {address!r}")
            port = int(port_text)
        slots_text = environ.get("SBM_PLAY_SLOTS")
        slots = defaults.slots
        if slots_text:
            if not slots_text.isdigit() or int(slots_text) < 1:
                raise ValueError(f"SBM_PLAY_SLOTS must be a positive whole number: {slots_text!r}")
            slots = int(slots_text)
        return cls(worker_id=defaults.worker_id, relay_host=host, relay_port=port, slots=slots)
