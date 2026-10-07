"""Bots that try to leave the jail; each exits with 42 if it gets anywhere (sandbox.md, E86)."""

import socket

import pytest
from sandbox_suite import REGULAR


@pytest.fixture
def listener():
    """Something on the runner's side that a bot without network must not reach."""
    with socket.create_server(("127.0.0.1", 47123)) as server:
        yield server


def test_no_network(play, listener):
    outcome = play("network")
    assert outcome.termination in REGULAR, outcome.detail


def test_no_files_outside_the_jail_and_nothing_writable(play):
    outcome = play("files")
    assert outcome.termination in REGULAR, outcome.detail


def test_no_new_processes(play):
    outcome = play("fork")
    assert outcome.termination in REGULAR, outcome.detail


def test_threads_stop_at_the_process_limit(play):
    outcome = play("threads")
    assert outcome.termination in REGULAR, outcome.detail
