import pytest

from sbm_runner.play.config import PlayConfig


def test_defaults_without_environment():
    config = PlayConfig.from_env({"SBM_WORKER_ID": "play-1"})
    assert (config.worker_id, config.relay_address, config.slots) == (
        "play-1",
        ("127.0.0.1", 9000),
        2,
    )


def test_address_and_slots_from_the_environment():
    config = PlayConfig.from_env({"SBM_RELAY_ADDRESS": "sbm-relay:9100", "SBM_PLAY_SLOTS": "4"})
    assert (config.relay_address, config.slots) == (("sbm-relay", 9100), 4)


@pytest.mark.parametrize(
    "environ",
    [{"SBM_RELAY_ADDRESS": "sbm-relay"}, {"SBM_RELAY_ADDRESS": ":9000"}, {"SBM_PLAY_SLOTS": "0"}],
)
def test_invalid_values_are_refused(environ):
    with pytest.raises(ValueError):
        PlayConfig.from_env(environ)
