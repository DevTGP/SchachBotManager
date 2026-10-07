"""Stopping the container hands the current game back to the queue instead of losing it."""

import signal


class Shutdown(BaseException):
    """Raised in the main thread on SIGTERM or SIGINT.

    It derives from BaseException so that no handler for ordinary errors swallows it.
    """


def install_handlers() -> None:
    def handle(signum: int, _frame: object) -> None:
        # A second signal must not interrupt the cleanup of the first.
        signal.signal(signum, signal.SIG_IGN)
        raise Shutdown(signal.Signals(signum).name)

    for signum in (signal.SIGTERM, signal.SIGINT):
        signal.signal(signum, handle)
