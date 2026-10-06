"""Referee core: plays one game between two players by protocol v1 (match-runner.md, E65).

Used by the local arena and by the server's runner; the players decide how bots are reached.
"""

from sbm.referee.match import Match
from sbm.referee.outcome import Outcome
from sbm.referee.player import LineTooLong, Player, PlayerClosed, PlayerTimeout
from sbm.referee.record import MatchRecord, MoveRecord, SideRecord
from sbm.referee.settings import STANDARD_FEN, MatchSettings

__all__ = [
    "STANDARD_FEN",
    "LineTooLong",
    "Match",
    "MatchRecord",
    "MatchSettings",
    "MoveRecord",
    "Outcome",
    "Player",
    "PlayerClosed",
    "PlayerTimeout",
    "SideRecord",
]
