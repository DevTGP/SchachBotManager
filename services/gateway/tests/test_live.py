"""The live channel end to end: a runner publishes moves, viewers read them as events."""

import json
import socket
import time
from dataclasses import replace

import pytest
from conftest import MATCH_ID, TIMEOUT, RunningGateway, WatchEnd, move

PATH = f"/api/v1/matches/{MATCH_ID}/live"


def raw_request(port: int) -> socket.socket:
    """Sends the request without waiting for the answer."""
    connection = socket.create_connection(("127.0.0.1", port), TIMEOUT)
    connection.sendall(f"GET {PATH} HTTP/1.1\r\n\r\n".encode())
    return connection


def wait_for(condition) -> None:
    deadline = time.monotonic() + TIMEOUT
    while not condition():
        assert time.monotonic() < deadline
        time.sleep(0.01)


def test_a_viewer_follows_the_match_from_its_ply_to_the_end(gateway):
    live = gateway.live()
    live.open()
    for ply in (1, 2, 3):
        live.move(ply)
    viewer = gateway.watch(f"{PATH}?after=1")
    assert viewer.status == 200
    assert viewer.headers["content-type"] == "text/event-stream; charset=utf-8"
    assert viewer.headers["cache-control"] == "no-store"
    assert viewer.headers["x-accel-buffering"] == "no"
    first = viewer.event()
    assert first["event"] == "move"
    assert first["id"] == "2"
    assert json.loads(first["data"]) == move(2)
    assert viewer.event()["id"] == "3"
    live.move(4)
    assert viewer.event()["id"] == "4"
    live.end()
    assert viewer.event() == {"event": "end", "data": "{}"}
    assert viewer.event() is None
    assert live.closed()
    viewer.close()
    live.close()


def test_last_event_id_resumes_after_a_reconnect(gateway):
    live = gateway.live()
    live.open()
    live.move(1)
    live.move(2)
    viewer = gateway.watch(f"{PATH}?after=0", headers="Last-Event-ID: 1\r\n")
    assert viewer.event()["id"] == "2"
    viewer.close()
    live.close()


def test_a_viewer_waits_briefly_for_the_runner(gateway):
    connection = raw_request(gateway.gateway.watch_port)
    time.sleep(0.1)
    live = gateway.live()
    live.open()
    live.move(1)
    viewer = WatchEnd(connection)
    assert viewer.status == 200
    assert viewer.event()["id"] == "1"
    viewer.close()
    live.close()


def test_a_match_nobody_publishes_is_not_live(gateway):
    viewer = gateway.watch(PATH)
    assert viewer.status == 404
    assert viewer.body()["code"] == "not_live"
    viewer.close()


def test_a_closed_runner_connection_ends_the_stream(gateway):
    live = gateway.live()
    live.open()
    viewer = gateway.watch(PATH)
    live.close()
    assert viewer.event() == {"event": "end", "data": "{}"}
    viewer.close()


def test_a_newer_runner_connection_ends_the_older_stream(gateway):
    older = gateway.live()
    older.open()
    older.move(1)
    viewer = gateway.watch(PATH)
    assert viewer.event()["id"] == "1"
    newer = gateway.live()
    newer.open()
    assert viewer.event()["event"] == "end"
    viewer.close()
    newer.move(1)
    again = gateway.watch(PATH)
    assert again.event()["id"] == "1"
    again.close()
    older.close()
    newer.close()


def test_a_runner_out_of_order_is_cut_off(gateway):
    live = gateway.live()
    live.open()
    viewer = gateway.watch(PATH)
    live.move(2)
    assert live.closed()
    assert viewer.event()["event"] == "end"
    viewer.close()
    live.close()


@pytest.mark.parametrize(
    "first", [b"{}\n", b'{"type":"open","v":2,"match_id":"' + MATCH_ID.encode() + b'"}\n']
)
def test_a_bad_open_is_refused(gateway, first):
    live = gateway.live()
    live.connection.sendall(first)
    assert live.closed()
    live.close()


@pytest.mark.parametrize(
    "method, target, status, code",
    [
        ("POST", PATH, 405, "method_not_allowed"),
        ("GET", "/api/v1/matches", 404, "not_found"),
        ("GET", f"{PATH}?after=x", 400, "invalid_request"),
    ],
)
def test_bad_requests_get_an_error_body(gateway, method, target, status, code):
    viewer = gateway.watch(target, method=method)
    assert viewer.status == status
    assert viewer.headers["content-type"] == "application/json"
    assert viewer.body()["code"] == code
    viewer.close()


def test_too_many_viewers_are_refused(config):
    running = RunningGateway(replace(config, max_watchers=1, feed_wait_seconds=2))
    try:
        first = raw_request(running.gateway.watch_port)
        wait_for(lambda: running.gateway.feeds.watchers == 1)
        second = running.watch(PATH)
        assert second.status == 503
        assert second.body()["code"] == "busy"
        second.close()
        first.close()
    finally:
        running.stop()


def test_stopping_closes_streams_without_end(config):
    running = RunningGateway(config)
    live = running.live()
    live.open()
    live.move(1)
    viewer = running.watch(PATH)
    assert viewer.event()["id"] == "1"
    running.stop()
    assert viewer.event() is None
    viewer.close()
    live.close()


def test_idle_streams_get_pings(config):
    running = RunningGateway(replace(config, watch_ping_seconds=0.05))
    live = running.live()
    live.open()
    viewer = running.watch(PATH)
    try:
        assert viewer.comment() == "retry: 3000"
        assert viewer.comment() == ""
        assert viewer.comment() == ": ping"
    finally:
        viewer.close()
        live.close()
        running.stop()
