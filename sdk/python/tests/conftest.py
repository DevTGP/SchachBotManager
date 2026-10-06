"""Every test starts with the default log state."""

import pytest

from sbm import INFO, log


@pytest.fixture(autouse=True)
def reset_log():
    log.configure(INFO, None)
    log.set_ply(None)
    yield
    log.configure(INFO, None)
    log.set_ply(None)
