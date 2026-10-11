import pytest

from sbm_runner.address import live_address, parse_address


def test_host_and_port():
    assert parse_address("SBM_LIVE_ADDRESS", "sbm-live:9001") == ("sbm-live", 9001)


@pytest.mark.parametrize("text", ["sbm-live", ":9001", "sbm-live:", "sbm-live:x", "sbm-live:0"])
def test_invalid_addresses_name_the_variable(text):
    with pytest.raises(ValueError, match="SBM_LIVE_ADDRESS must be host:port"):
        parse_address("SBM_LIVE_ADDRESS", text)


def test_live_address_is_optional():
    assert live_address({}) is None
    assert live_address({"SBM_LIVE_ADDRESS": ""}) is None
    assert live_address({"SBM_LIVE_ADDRESS": "127.0.0.1:9001"}) == ("127.0.0.1", 9001)
