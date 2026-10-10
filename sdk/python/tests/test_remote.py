"""Transport remote (E116): options, the request for a game, the WebSocket client and a game."""

import json
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest
from remote_fakes import GAME, MATCH_ID, SEAT, TOKEN, FakeGateway

import sbm
from sbm.options import OptionsError, RemoteOptions, parse_options
from sbm.remote import game_request
from sbm.remote.channel import RemoteChannel
from sbm.remote.game_request import RemoteError, Seat, request_game
from sbm.remote.websocket import WebSocket

# Options


def test_remote_options_from_arguments_and_environment():
    options = parse_options(
        ["--remote", "https://example.org", "--opponent", "Material", "--time", "30+0.5"],
        {"SBM_TOKEN": TOKEN, "SBM_COLOR": "Black"},
    )
    assert options.transport == "remote"
    assert options.remote == RemoteOptions(
        url="https://example.org", token=TOKEN, opponent="Material", color="black", time="30+0.5"
    )


def test_remote_through_the_environment_alone():
    environ = {
        "SBM_TRANSPORT": "remote",
        "SBM_REMOTE_URL": "https://example.org",
        "SBM_TOKEN": TOKEN,
        "SBM_OPPONENT": "Random",
        "SBM_DISCIPLINE": "Blitz",
    }
    remote = parse_options([], environ).remote
    assert (remote.opponent, remote.discipline, remote.color) == ("Random", "Blitz", "random")


@pytest.mark.parametrize(
    "argv",
    [
        ["--remote", "https://example.org", "--opponent", "Material"],
        ["--remote", "https://example.org", "--token", TOKEN],
        ["--remote", "https://example.org", "--token", TOKEN, "--opponent", "M", "--color", "red"],
    ],
)
def test_incomplete_remote_options(argv):
    with pytest.raises(OptionsError):
        parse_options(argv, {})


def test_the_remote_names_are_left_to_the_bot_otherwise():
    assert parse_options(["--color", "red", "--time", "x"], {}).remote is None


# The request for a game


class FakeApi(BaseHTTPRequestHandler):
    status = 201
    answer: dict = {}
    seen: list = []

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        headers = {name.lower(): value for name, value in self.headers.items()}
        FakeApi.seen.append((self.path, headers, body))
        data = json.dumps(FakeApi.answer).encode()
        self.send_response(FakeApi.status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, *_args):
        pass


@pytest.fixture
def fake_api():
    FakeApi.seen = []
    server = ThreadingHTTPServer(("127.0.0.1", 0), FakeApi)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{server.server_address[1]}"
    server.shutdown()


def test_request_game_sends_the_token_and_names_the_socket(fake_api):
    FakeApi.status = 201
    FakeApi.answer = {
        "match_id": MATCH_ID,
        "seat": SEAT,
        "color": "white",
        "socket_path": "/api/v1/play/socket",
    }

    seat = request_game(fake_api + "/", TOKEN, {"opponent": "Material", "color": "white"})

    assert seat == Seat(
        MATCH_ID, SEAT, "white", fake_api.replace("http", "ws") + "/api/v1/play/socket"
    )
    path, headers, body = FakeApi.seen[0]
    assert path == "/api/v1/remote/matches"
    assert headers["authorization"] == f"Bearer {TOKEN}"
    assert headers["x-sbm-csrf"] == "1"
    assert body == {"opponent": "Material", "color": "white"}


def test_request_game_reports_the_apis_error(fake_api):
    FakeApi.status = 429
    FakeApi.answer = {"code": "too_many_games", "message": "finish your running game"}
    with pytest.raises(RemoteError) as raised:
        request_game(fake_api, TOKEN, {})
    assert raised.value.code == "too_many_games"


def test_request_game_needs_http(fake_api):
    with pytest.raises(RemoteError):
        request_game("ftp://example.org", TOKEN, {})


# A game against the fake gateway


def test_websocket_messages_and_close():
    gateway = FakeGateway(GAME)
    try:
        socket = WebSocket.connect(gateway.url)
        socket.send_text(json.dumps({"type": "join", "v": 1, "match_id": MATCH_ID, "seat": SEAT}))
        assert json.loads(socket.receive_text(5))["type"] == "joined"
        assert json.loads(socket.receive_text(5))["type"] == "init"
        socket.close()
    finally:
        gateway.stop()


def test_a_refused_seat_is_an_error():
    gateway = FakeGateway(GAME)
    try:
        with pytest.raises(RemoteError) as raised:
            RemoteChannel.join(Seat(MATCH_ID, "B" * 43, "white", gateway.url))
        assert raised.value.code == "no_game"
    finally:
        gateway.stop()


class SlowBot(sbm.Bot):
    """Thinks longer than the gateway waits for a pong, so the SDK must answer pings itself."""

    def choose_move(self, board, clock):
        time.sleep(1.5)
        return board.legal_moves()[0]


def test_run_plays_a_remote_game_and_answers_pings(monkeypatch):
    gateway = FakeGateway(GAME, ping=0.3)
    seats = []

    def fake_request(url, token, body):
        seats.append((url, token, body))
        return Seat(MATCH_ID, SEAT, "white", gateway.url)

    monkeypatch.setattr(game_request, "request_game", fake_request)
    monkeypatch.setattr(
        sys,
        "argv",
        ["bot.py", "--remote", "https://example.org", "--opponent", "Material", "--time", "60+1"],
    )
    monkeypatch.setenv("SBM_TOKEN", TOKEN)
    try:
        sbm.run(SlowBot)
    finally:
        gateway.stop()

    assert seats == [
        (
            "https://example.org",
            TOKEN,
            {
                "opponent": "Material",
                "color": "random",
                "initial_time_ms": 60_000,
                "increment_ms": 1000,
            },
        )
    ]
    kinds = [message["type"] for message in gateway.received]
    assert kinds == ["join", "ready", "move"]
