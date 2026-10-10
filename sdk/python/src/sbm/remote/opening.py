"""Opens a remote game: asks the web API for it and takes the seat (E116)."""

from sbm.arena.time_control import parse_time_control
from sbm.log import Log
from sbm.options import RemoteOptions
from sbm.remote import game_request
from sbm.remote.channel import RemoteChannel
from sbm.remote.game_request import RemoteError, Seat


def request_body(remote: RemoteOptions) -> dict:
    """The body of POST /remote/matches; a discipline wins over the time."""
    body = {"opponent": remote.opponent, "color": remote.color}
    if remote.discipline:
        return body | {"discipline": remote.discipline}
    try:
        initial_ms, increment_ms = parse_time_control(remote.time)
    except ValueError as error:
        raise RemoteError(str(error), "usage") from None
    return body | {"initial_time_ms": initial_ms, "increment_ms": increment_ms}


def open_game(remote: RemoteOptions) -> tuple[Seat, RemoteChannel]:
    """Raises RemoteError if the server refuses the game or the seat."""
    body = request_body(remote)
    seat = game_request.request_game(remote.url, remote.token, body)
    Log.info(f"remote game {seat.match_id} against {remote.opponent}, playing {seat.color}")
    return seat, RemoteChannel.join(seat)
