"""play with a server (E120): games against a bot on the site, through the fake gateway."""

import pytest
from remote_fakes import GAME, MATCH_ID, SEAT, TOKEN, FakeGateway

import sbm
from sbm import WHITE, InvalidArgumentError, PlayedGame
from sbm.remote import game_request, remote_game
from sbm.remote.game_request import RemoteError, Seat

SERVER = "https://example.org"


class First(sbm.Bot):
    def choose_move(self, board, clock):
        return board.legal_moves()[0]


@pytest.fixture
def gateway():
    gateway = FakeGateway(GAME)
    yield gateway
    gateway.stop()


@pytest.fixture
def requests(monkeypatch, gateway):
    """Answers each request for a game with the fake gateway's seat; refusals come first."""
    seen = []
    refusals = []

    def fake_request(url, token, body):
        seen.append((url, token, body))
        if refusals:
            raise refusals.pop(0)
        return Seat(MATCH_ID, SEAT, body["color"], gateway.url)

    monkeypatch.setattr(game_request, "request_game", fake_request)
    monkeypatch.setattr(remote_game, "BUSY_WAIT_SECONDS", 0)
    return seen, refusals


def test_play_on_the_server_alternates_colors(requests):
    seen, _ = requests
    played = sbm.play(First, "Material", server=SERVER, token=TOKEN, color="black", games=2)

    assert [body["color"] for _, _, body in seen] == ["black", "white"]
    assert seen[0] == (
        SERVER,
        TOKEN,
        {"opponent": "Material", "color": "black", "initial_time_ms": 60_000, "increment_ms": 1000},
    )
    # The fake gateway always sends the same init and game_over.
    assert played == [PlayedGame(MATCH_ID, WHITE, "Stockfisch Junior", "0-1", "checkmate")] * 2


def test_the_token_can_come_from_the_environment(requests, monkeypatch):
    seen, _ = requests
    monkeypatch.setenv("SBM_TOKEN", TOKEN)
    sbm.play(First, "Material", server=SERVER, discipline="Blitz")

    assert seen[0][1] == TOKEN
    assert seen[0][2]["discipline"] == "Blitz"
    assert "initial_time_ms" not in seen[0][2]


def test_play_waits_while_the_previous_game_ends(requests):
    seen, refusals = requests
    refusals.append(RemoteError("finish your running game", "too_many_games"))
    [game] = sbm.play(First, "Material", server=SERVER, token=TOKEN)

    assert len(seen) == 2
    assert game.termination == "checkmate"


def test_a_refused_game_ends_the_process(requests, capsys):
    _, refusals = requests
    refusals.append(RemoteError("the server refused the game (unknown_bot): ?", "unknown_bot"))
    with pytest.raises(SystemExit) as raised:
        sbm.play(First, "Nobody", server=SERVER, token=TOKEN)
    assert raised.value.code == 1
    assert "unknown_bot" in capsys.readouterr().err


@pytest.mark.parametrize(
    "arguments",
    [
        {"server": "ftp://example.org", "token": TOKEN},
        {"server": SERVER},
        {"server": SERVER, "token": TOKEN, "time": "60+1", "discipline": "Blitz"},
        {"server": SERVER, "token": TOKEN, "time": "soon"},
    ],
)
def test_invalid_remote_arguments(arguments, monkeypatch):
    monkeypatch.delenv("SBM_TOKEN", raising=False)
    with pytest.raises(InvalidArgumentError):
        sbm.play(First, "Material", **arguments)
