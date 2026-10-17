"""Bots that try to leave the jail; each exits with 42 if it gets anywhere (sandbox.md, E86)."""

import socket

import pytest
from sandbox_suite import LANGUAGES, REGULAR

from sbm_runner.sandbox.runtimes import JAVASCRIPT


@pytest.fixture
def listener():
    """Something on the runner's side that a bot without network must not reach."""
    with socket.create_server(("127.0.0.1", 47123)) as server:
        yield server


@pytest.mark.parametrize("language", LANGUAGES)
def test_no_network(play, listener, language):
    outcome = play("network", language=language)
    assert outcome.termination in REGULAR, outcome.detail


@pytest.mark.parametrize("language", LANGUAGES)
def test_no_files_outside_the_jail_and_nothing_writable(play, language):
    outcome = play("files", language=language)
    assert outcome.termination in REGULAR, outcome.detail


@pytest.mark.parametrize("language", LANGUAGES)
def test_no_new_processes(play, language):
    outcome = play("fork", language=language)
    assert outcome.termination in REGULAR, outcome.detail


def test_threads_stop_at_the_process_limit(play):
    outcome = play("threads")
    assert outcome.termination in REGULAR, outcome.detail


def test_no_code_from_strings_and_no_webassembly(play):
    outcome = play("codegen", language=JAVASCRIPT)
    assert outcome.termination in REGULAR, outcome.detail
