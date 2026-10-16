"""C# bots against the jail: the same attacks as in Python, from a compiled program (E205).

Each bot in bots/csharp exits with 42 if it gets anywhere (sandbox.md); none passed the analysis.
"""

import socket

import pytest
from sandbox_suite import REGULAR


@pytest.fixture
def listener():
    """Something on the runner's side that a bot without network must not reach."""
    with socket.create_server(("127.0.0.1", 47123)) as server:
        yield server


def test_no_network(play_csharp, listener):
    outcome = play_csharp("Network")
    assert outcome.termination in REGULAR, outcome.detail


@pytest.mark.parametrize("name", ["Files", "Processes", "Syscalls"])
def test_no_way_out_of_the_jail(play_csharp, name):
    outcome = play_csharp(name)
    assert outcome.termination in REGULAR, outcome.detail


def test_threads_stop_at_the_process_limit(play_csharp):
    outcome = play_csharp("Threads")
    assert outcome.termination in REGULAR, outcome.detail


def test_native_memory_hits_the_memory_limit(play_csharp):
    outcome = play_csharp("NativeMemory")
    assert (outcome.result, outcome.termination) == ("0-1", "memory_limit"), outcome.detail


def test_the_managed_heap_ends_below_the_memory_limit(play_csharp):
    """The GC's hard limit throws OutOfMemoryException first, which ends the bot as a crash."""
    outcome = play_csharp("ManagedMemory")
    assert (outcome.result, outcome.termination) == ("0-1", "crash"), outcome.detail
