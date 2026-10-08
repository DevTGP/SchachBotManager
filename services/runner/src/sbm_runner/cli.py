"""Entry point sbm-runner; configured by environment variables, as in the container."""

import logging
import os
import sys
from functools import partial

from pymongo.database import Database
from sbm_store.connection import database_from_env

from sbm_runner.checkout import checkout
from sbm_runner.config import RunnerConfig, default_worker_id
from sbm_runner.players import plain_player
from sbm_runner.sandbox.jail import Sandbox, SandboxBroken
from sbm_runner.sandbox.settings import NONE, SandboxSettings
from sbm_runner.shutdown import Shutdown, install_handlers
from sbm_runner.worker import Worker

log = logging.getLogger("sbm_runner")


def main() -> int:
    logging.basicConfig(
        level=os.environ.get("SBM_LOG_LEVEL", "INFO"),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        stream=sys.stderr,
    )
    install_handlers()
    config = RunnerConfig(worker_id=os.environ.get("SBM_WORKER_ID") or default_worker_id())
    try:
        settings = SandboxSettings.from_env(os.environ)
        db = database_from_env(os.environ)
        sandbox = start_sandbox(settings, db)
        log.info("runner %s started", config.worker_id)
        if sandbox is None:
            Worker(db, config, players=plain_player).run()
        else:
            Worker(db, config, players=sandbox.player, verifier=sandbox).run()
    except (ValueError, SandboxBroken) as error:
        log.error("runner %s cannot start: %s", config.worker_id, error)
        return 1
    except Shutdown as signal_name:
        log.info("runner %s stopped by %s", config.worker_id, signal_name)
    return 0


def start_sandbox(settings: SandboxSettings, db: Database) -> Sandbox | None:
    """None without a sandbox: then only the reference bots play and no bot is verified."""
    if settings.mode == NONE:
        log.warning("no sandbox (SBM_SANDBOX=none): only the reference bots play, no verification")
        return None
    sandbox = Sandbox(settings, files=partial(checkout, db))
    sandbox.prepare()
    log.info("sandbox %s ready, runtime %s", settings.mode, sandbox.runtime)
    return sandbox


if __name__ == "__main__":
    sys.exit(main())
