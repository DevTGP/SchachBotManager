"""Entry point sbm-gateway; configured by environment variables, as in the container."""

import asyncio
import logging
import os
import signal
import sys

from sbm_gateway.config import GatewayConfig
from sbm_gateway.server import Gateway

log = logging.getLogger("sbm_gateway")


async def run(config: GatewayConfig) -> None:
    gateway = Gateway(config)
    await gateway.start()
    log.info(
        "gateway listening: clients on port %d, relay on %s:%d",
        gateway.socket_port,
        config.relay_host,
        gateway.relay_port,
    )
    stop = asyncio.Event()
    loop = asyncio.get_running_loop()
    for signum in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(signum, stop.set)
    await stop.wait()
    log.info("gateway stopping")
    await gateway.stop()


def main() -> int:
    logging.basicConfig(
        level=os.environ.get("SBM_LOG_LEVEL", "INFO"),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        stream=sys.stderr,
    )
    try:
        config = GatewayConfig.from_env(os.environ)
    except ValueError as error:
        log.error("gateway cannot start: %s", error)
        return 1
    asyncio.run(run(config))
    return 0


if __name__ == "__main__":
    sys.exit(main())
