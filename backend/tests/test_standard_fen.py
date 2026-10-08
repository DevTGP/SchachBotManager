"""The store keeps its own copy of the standard position for is_rated (E100)."""

from sbm import referee
from sbm_store import discipline


def test_the_store_and_the_referee_agree():
    assert discipline.STANDARD_FEN == referee.STANDARD_FEN
