"""Start options from the command line and environment (E61)."""

import pytest

import sbm
from sbm.options import DEFAULT_PORT, Options, OptionsError, parse_options


def test_defaults():
    assert parse_options([], {}) == Options("stdio", DEFAULT_PORT, sbm.INFO, None)


def test_environment():
    environ = {
        "SBM_TRANSPORT": "TCP",
        "SBM_PORT": "9000",
        "SBM_LOG_LEVEL": "debug",
        "SBM_LOG_FILE": "bot.log",
    }
    assert parse_options([], environ) == Options("tcp", 9000, sbm.DEBUG, "bot.log")


def test_arguments_win_over_environment():
    environ = {"SBM_PORT": "9000", "SBM_LOG_LEVEL": "debug", "SBM_LOG_FILE": "env.log"}
    argv = ["--tcp", "7000", "--log-level=Off", "--log-file", "arg.log"]
    assert parse_options(argv, environ) == Options("tcp", 7000, sbm.OFF, "arg.log")


def test_tcp_without_port():
    assert parse_options(["--tcp"], {}) == Options("tcp", DEFAULT_PORT, sbm.INFO, None)
    assert parse_options(["--tcp"], {"SBM_PORT": "9000"}).port == 9000
    assert parse_options(["--tcp", "--log-level", "warn"], {}).port == DEFAULT_PORT


def test_other_arguments_belong_to_the_bot():
    argv = ["--depth", "4", "book.bin", "--log-level", "error", "-v"]
    assert parse_options(argv, {}) == Options(log_level=sbm.ERROR)


@pytest.mark.parametrize(
    ("argv", "environ"),
    [
        (["--tcp", "0"], {}),
        (["--tcp", "65536"], {}),
        (["--tcp", "port"], {}),
        (["--log-level", "loud"], {}),
        (["--log-level"], {}),
        ([], {"SBM_TRANSPORT": "remote"}),
        ([], {"SBM_PORT": "-1"}),
        ([], {"SBM_LOG_LEVEL": "5"}),
    ],
)
def test_invalid_values(argv, environ):
    with pytest.raises(OptionsError):
        parse_options(argv, environ)
