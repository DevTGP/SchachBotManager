"""Reads the HTTP request of a viewer: GET /api/v1/matches/{id}/live (E142).

Only the frontend's nginx reaches the watch port, so the gateway reads just the request line
and the headers it needs and answers anything else with an error.
"""

from dataclasses import dataclass
from http import HTTPStatus
from urllib.parse import parse_qs, urlsplit

from sbm_gateway.config import WATCH_PATH

# Head of the request, request line and headers; nginx sends far less.
HEAD_LIMIT = 8 * 1024
# A ply above this cannot come from a game the gateway keeps.
_MAX_PLY_DIGITS = 6


class BadRequest(Exception):
    def __init__(self, status: HTTPStatus, code: str, text: str) -> None:
        super().__init__(text)
        self.status = status
        self.code = code


@dataclass(frozen=True)
class WatchRequest:
    match_id: str
    # The viewer has the moves up to this ply; the stream starts after it.
    after: int


def parse_head(head: bytes) -> WatchRequest:
    """head ends with the blank line. Last-Event-ID, sent by a reconnecting EventSource, wins
    over the query parameter after."""
    lines = head.decode("latin-1").split("\r\n")
    parts = lines[0].split(" ")
    if len(parts) != 3 or not parts[2].startswith("HTTP/1."):
        raise BadRequest(HTTPStatus.BAD_REQUEST, "invalid_request", "not an HTTP/1 request")
    method, target, _version = parts
    url = urlsplit(target)
    match = WATCH_PATH.fullmatch(url.path)
    if match is None:
        raise BadRequest(HTTPStatus.NOT_FOUND, "not_found", "no such resource")
    if method != "GET":
        raise BadRequest(HTTPStatus.METHOD_NOT_ALLOWED, "method_not_allowed", "only GET")
    after = _ply(parse_qs(url.query).get("after", ["0"])[-1])
    for line in lines[1:]:
        name, _, value = line.partition(":")
        if name.strip().lower() == "last-event-id" and value.strip():
            after = _ply(value.strip())
    return WatchRequest(match.group(1), after)


def _ply(text: str) -> int:
    if not text.isascii() or not text.isdigit() or len(text) > _MAX_PLY_DIGITS:
        raise BadRequest(HTTPStatus.BAD_REQUEST, "invalid_request", "after must be a ply")
    return int(text)
