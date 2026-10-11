from http import HTTPStatus

import pytest
from conftest import MATCH_ID

from sbm_gateway.watch_request import BadRequest, WatchRequest, parse_head

PATH = f"/api/v1/matches/{MATCH_ID}/live"


def head(request_line: str, *headers: str) -> bytes:
    return "\r\n".join([request_line, *headers, "", ""]).encode("latin-1")


def refusal(data: bytes) -> tuple[HTTPStatus, str]:
    with pytest.raises(BadRequest) as error:
        parse_head(data)
    return error.value.status, error.value.code


def test_the_viewer_names_the_match_and_the_ply_it_has():
    assert parse_head(head(f"GET {PATH}?after=12 HTTP/1.1")) == WatchRequest(MATCH_ID, 12)


def test_without_after_the_stream_starts_with_the_first_move():
    assert parse_head(head(f"GET {PATH} HTTP/1.0", "Host: sbm")).after == 0


def test_last_event_id_wins_over_after():
    data = head(f"GET {PATH}?after=3 HTTP/1.1", "Host: sbm", "last-event-id: 17")
    assert parse_head(data).after == 17


def test_an_empty_last_event_id_keeps_after():
    assert parse_head(head(f"GET {PATH}?after=3 HTTP/1.1", "Last-Event-ID: ")).after == 3


@pytest.mark.parametrize(
    "data, expected",
    [
        (head("GET /api/v1/matches HTTP/1.1"), (HTTPStatus.NOT_FOUND, "not_found")),
        (head(f"GET {PATH.upper()} HTTP/1.1"), (HTTPStatus.NOT_FOUND, "not_found")),
        (head(f"GET {PATH}/more HTTP/1.1"), (HTTPStatus.NOT_FOUND, "not_found")),
        (
            head(f"POST {PATH} HTTP/1.1"),
            (HTTPStatus.METHOD_NOT_ALLOWED, "method_not_allowed"),
        ),
        (head(f"GET {PATH}?after=-1 HTTP/1.1"), (HTTPStatus.BAD_REQUEST, "invalid_request")),
        (head(f"GET {PATH}?after=1234567 HTTP/1.1"), (HTTPStatus.BAD_REQUEST, "invalid_request")),
        (head(f"GET {PATH}?after=%C2%B2 HTTP/1.1"), (HTTPStatus.BAD_REQUEST, "invalid_request")),
        (
            head(f"GET {PATH} HTTP/1.1", "Last-Event-ID: x"),
            (HTTPStatus.BAD_REQUEST, "invalid_request"),
        ),
        (head(f"GET {PATH}"), (HTTPStatus.BAD_REQUEST, "invalid_request")),
        (head(f"GET {PATH} HTTP/2"), (HTTPStatus.BAD_REQUEST, "invalid_request")),
        (head(f"GET  {PATH} HTTP/1.1"), (HTTPStatus.BAD_REQUEST, "invalid_request")),
    ],
)
def test_other_requests_are_refused(data, expected):
    assert refusal(data) == expected
