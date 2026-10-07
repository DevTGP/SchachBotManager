"""Bots that use up resources; the sandbox stops them and the referee scores it (sandbox.md)."""

from sandbox_suite import REGULAR
from sbm.referee import MatchSettings


def test_memory_limit(play):
    outcome = play("memory")
    assert (outcome.result, outcome.termination) == ("0-1", "memory_limit"), outcome.detail


def test_endless_loop_loses_on_time_and_is_killed(play):
    outcome = play("endless_loop", MatchSettings(initial_time_ms=1_000, increment_ms=0))
    assert (outcome.result, outcome.termination) == ("0-1", "timeout"), outcome.detail


def test_overlong_line_is_a_protocol_violation(play):
    outcome = play("long_line")
    assert (outcome.result, outcome.termination) == ("0-1", "protocol_violation")
    assert "line_too_long" in outcome.detail


def test_flood_on_stderr_does_not_block_the_bot(play):
    outcome = play("stderr_flood")
    assert outcome.termination in REGULAR, outcome.detail
