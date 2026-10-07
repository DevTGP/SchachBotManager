"""Tries to reach anything over a socket; exits with 42 if it gets through (sandbox.md)."""

import os
import socket

import sbm

TARGETS = [
    (socket.AF_INET, ("1.1.1.1", 53)),
    (socket.AF_INET, ("127.0.0.1", 47123)),
    (socket.AF_INET6, ("2606:4700:4700::1111", 53)),
    (socket.AF_UNIX, "/var/run/docker.sock"),
]


def reachable(family: int, address) -> bool:
    try:
        with socket.socket(family, socket.SOCK_STREAM) as connection:
            connection.settimeout(2)
            connection.connect(address)
    except OSError:
        return False
    return True


class Network(sbm.Bot):
    def choose_move(self, board: sbm.Board, clock: sbm.Clock) -> sbm.Move:
        if any(reachable(family, address) for family, address in TARGETS):
            os._exit(42)
        return board.legal_moves()[0]


if __name__ == "__main__":
    sbm.run(Network)
