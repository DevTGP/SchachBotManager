"""Entry point sbm-runner; configured by environment variables, as in the container."""

import logging
import os
import sys

from sbm_store.connection import database_from_env

from sbm_runner.config import RunnerConfig, default_worker_id
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
        db = database_from_env(os.environ)
        log.info("runner %s started", config.worker_id)
        Worker(db, config).run()
    except Shutdown as signal_name:
        log.info("runner %s stopped by %s", config.worker_id, signal_name)
    return 0


if __name__ == "__main__":
    sys.exit(main())
