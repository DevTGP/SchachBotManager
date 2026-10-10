"""A whole game through the referee: startup, turns, clock, every kind of ending."""

import pytest
from protocol_schemas import violations
from scripted_player import Early, FakeTime, Reply, ScriptedPlayer, move, ready, resign

from sbm.referee import LineTooLong, Match, MatchSettings, PlayerClosed

FOOLS_MATE_WHITE = [move("f2f3"), move("g2g4")]
FOOLS_MATE_BLACK = [move("e7e5"), move("d8h4")]
NS_PER_MS = 1_000_000


def play(white_script, black_script, **settings):
    time = FakeTime()
    white = ScriptedPlayer("White Bot", time, white_script)
    black = ScriptedPlayer("Black Bot", time, black_script)
    match = Match(white, black, MatchSettings(**({"initial_time_ms": 1000} | settings)), now=time)
    record = match.play()
    for player in (white, black):
        for message in player.sent:
            assert violations("referee_message", message) == [], message
        assert player.events[-1] == ("close",)
    return record, white, black


def ending(record):
    return record.outcome.result, record.outcome.termination


def error_codes(player):
    return [message["code"] for message in player.sent if message["type"] == "error"]


def test_fools_mate():
    record, white, black = play(
        [ready(), *FOOLS_MATE_WHITE],
        [ready(sdk="2.1.0-beta", lang="cpp"), *FOOLS_MATE_BLACK],
    )
    assert ending(record) == ("0-1", "checkmate")
    assert record.outcome.winner == 1
    assert [m.san for m in record.moves] == ["f3", "e5", "g4", "Qh4#"]
    assert [m.ply for m in record.moves] == [1, 2, 3, 4]
    assert record.moves[-1].fen.startswith("rnb1kbnr/pppp1ppp/8/4p3/6Pq/5P2/PPPPP2P/RNBQKBNR w")
    assert (record.white.sdk, record.white.lang) == ("1.0.0", "python")
    assert (record.black.sdk, record.black.lang) == ("2.1.0-beta", "cpp")
    assert white.sent_types() == ["init", "turn", "turn", "game_over"]
    assert black.sent_types() == ["init", "turn", "turn", "game_over"]
    assert (
        black.sent[-1]
        == white.sent[-1]
        == {
            "type": "game_over",
            "result": "0-1",
            "termination": "checkmate",
            "last_move": "d8h4",
            "fen": record.moves[-1].fen,
            "ply": 4,
        }
    )


def test_init_and_turn_messages():
    _, white, black = play(
        [ready(), *FOOLS_MATE_WHITE], [ready(), *FOOLS_MATE_BLACK], game_id="g-7", increment_ms=5
    )
    init = black.sent[0]
    assert (init["color"], init["opponent_name"], init["game_id"]) == ("black", "White Bot", "g-7")
    assert white.sent[0]["opponent_name"] == "Black Bot"
    first, second = white.sent[1], black.sent[1]
    assert (first["last_move"], first["ply"]) == (None, 0)
    assert (second["last_move"], second["ply"]) == ("f2f3", 1)
    assert second["fen"] == "rnbqkbnr/pppppppp/8/8/8/5P2/PPPPP1PP/RNBQKBNR b KQkq - 0 1"
    assert white.sent[2]["last_move"] == "e7e5"


def test_hook_order():
    _, white, _ = play([ready(), *FOOLS_MATE_WHITE], [ready(), *FOOLS_MATE_BLACK])
    calls = [event[0] if event[0] != "send" else event[1]["type"] for event in white.events]
    turn = ["resume", "receive", "turn", "receive", "suspend"]
    assert calls == [
        "start", "init", "receive", "suspend", *turn, *turn, "resume", "game_over", "close"
    ]  # fmt: skip


def test_black_opens_a_custom_position():
    record, white, black = play(
        [ready(), move("e1d1")],
        [ready(), move("e8d8"), resign()],
        start_fen="4k3/8/8/8/8/8/8/R3K3 b - - 0 1",
    )
    assert ending(record) == ("1-0", "resignation")
    assert black.sent[1]["last_move"] is None
    assert white.sent[1]["last_move"] == "e8d8"
    assert [m.ply for m in record.moves] == [1, 2]


def test_clock_and_increment():
    record, white, black = play(
        [ready(), Reply(move("f2f3"), 300), Reply(move("g2g4"), 815)],
        [ready(), Reply(move("e7e5"), 50), move("d8h4")],
        initial_time_ms=1000,
        increment_ms=100,
        tolerance_ms=20,
    )
    assert [m.elapsed_ms for m in record.moves] == [300, 50, 815, 0]
    # 1000 - 300 + 100; then 800 - 815 is within the tolerance and floors at 0.
    assert [m.remaining_ms for m in record.moves] == [800, 1050, 100, 1150]
    assert black.sent[1]["remaining_ms"] == 1000
    assert black.sent[1]["opponent_remaining_ms"] == 800
    assert white.sent[2]["remaining_ms"] == 800


def test_deadline_covers_remaining_time_and_tolerance():
    _, white, _ = play([ready(), *FOOLS_MATE_WHITE], [ready(), *FOOLS_MATE_BLACK], tolerance_ms=20)
    # Startup, then poll and turn for each move; the fake clock stays at 0 in this game.
    turn_deadlines = [event[1] for event in white.events if event[0] == "receive"][2::2]
    assert turn_deadlines == [1020 * NS_PER_MS] * 2


def test_timeout():
    record, white, black = play(
        [ready(), Reply(move("e2e4"), 1021)], [ready()], initial_time_ms=1000, tolerance_ms=20
    )
    assert ending(record) == ("0-1", "timeout")
    assert white.sent_types() == ["init", "turn"]
    assert black.sent_types() == ["init", "game_over"]
    final = black.sent[-1]
    assert (final["last_move"], final["fen"], final["ply"]) == (None, record.start_fen, 0)


def test_waiting_line_after_the_deadline_is_a_timeout():
    record, *_ = play(
        [ready(), Reply(move("e2e4"), 1021, waiting=True)], [ready()], initial_time_ms=1000
    )
    assert ending(record) == ("0-1", "timeout")


def test_tolerance_is_not_a_timeout():
    record, *_ = play(
        [ready(), Reply(move("e2e4"), 1020), resign()], [ready(), resign()], initial_time_ms=1000
    )
    assert ending(record) == ("1-0", "resignation")
    assert record.moves[0].remaining_ms == 0


def test_timeout_against_a_bare_king_is_a_draw():
    record, *_ = play(
        [ready(), Reply(move("a1a2"), 2000)], [ready()], start_fen="4k3/8/8/8/8/8/8/Q3K3 w - - 0 1"
    )
    assert ending(record) == ("1/2-1/2", "timeout_insufficient_material")


def test_without_clock_nothing_times_out():
    record, white, _ = play(
        [ready(), Reply(move("f2f3"), 10**9), *FOOLS_MATE_WHITE[1:]],
        [Reply(ready(), 10**9), *FOOLS_MATE_BLACK],
        clock=False,
    )
    assert ending(record) == ("0-1", "checkmate")
    deadlines = [event[1] for event in white.events if event[0] == "receive"]
    assert deadlines[0] is None
    assert deadlines[2::2] == [None, None]
    assert [m.remaining_ms for m in record.moves] == [1000] * 4


def test_illegal_move():
    record, white, black = play([ready(), move("e2e5")], [ready()])
    assert ending(record) == ("0-1", "illegal_move")
    assert "e2e5" in record.outcome.detail
    assert error_codes(white) == ["illegal_move"]
    assert white.sent_types() == ["init", "turn", "error", "game_over"]
    assert black.sent_types() == ["init", "game_over"]


def test_promotion_needs_the_piece():
    fen = "8/4P3/8/8/8/8/k7/4K3 w - - 0 1"
    record, *_ = play([ready(), move("e7e8")], [ready()], start_fen=fen)
    assert ending(record) == ("0-1", "illegal_move")
    record, *_ = play([ready(), move("e7e8q"), resign()], [ready(), move("a2a1")], start_fen=fen)
    assert record.moves[0].san == "e8=Q"


@pytest.mark.parametrize(
    ("line", "code"),
    [
        (b"{", "invalid_json"),
        ({"type": "draw", "v": 1}, "unknown_type"),
        (move("e2e4") | {"extra": 1}, "schema_violation"),
        (move("E2E4"), "schema_violation"),
        (ready(), "unexpected_message"),
        (LineTooLong(), "line_too_long"),
    ],
)
def test_protocol_violation_in_a_turn(line, code):
    record, white, _ = play([ready(), line], [ready()])
    assert ending(record) == ("0-1", "protocol_violation")
    assert error_codes(white) == [code]
    assert white.sent_types()[-1] == "game_over"


def test_message_outside_the_own_turn():
    record, _, black = play([ready(), move("e2e4")], [ready(), Early(move("e7e5"))])
    assert ending(record) == ("1-0", "protocol_violation")
    assert error_codes(black) == ["unexpected_message"]
    assert len(record.moves) == 1


def test_info_is_recorded_normalized():
    record, *_ = play(
        [ready(), move("e2e4", depth=3.0, score_cp=-12, pv=["e2e4"]), resign()],
        [ready(), resign()],
    )
    assert record.moves[0].info == {"depth": 3, "score_cp": -12, "pv": ["e2e4"]}


@pytest.mark.parametrize("termination", ["crash", "memory_limit"])
def test_player_leaves_during_a_turn(termination):
    record, white, black = play([ready(), PlayerClosed("exit code 1", termination)], [ready()])
    assert ending(record) == ("0-1", termination)
    assert white.sent_types() == ["init", "turn"]
    assert black.sent_types() == ["init", "game_over"]


def test_player_closing_while_receiving_game_over_does_not_matter():
    class Leaving(ScriptedPlayer):
        def send(self, message):
            if message["type"] == "game_over":
                raise PlayerClosed("gone")
            super().send(message)

    time = FakeTime()
    white = Leaving("W", time, [ready(), resign()])
    black = ScriptedPlayer("B", time, [ready()])
    record = Match(white, black, MatchSettings(initial_time_ms=1000), now=time).play()
    assert ending(record) == ("0-1", "resignation")
    assert black.sent_types()[-1] == "game_over"


def test_startup_timeout_of_one_side():
    record, white, black = play([Reply(ready(), 10_001)], [ready()], startup_ms=10_000)
    assert ending(record) == ("0-1", "startup_timeout")
    assert white.sent_types() == ["init"]
    assert white.events[-2:] == [("suspend",), ("close",)]
    assert black.sent_types() == ["init", "game_over"]
    assert record.white.sdk is None


def test_startup_waiting_ready_after_the_budget_is_a_timeout():
    record, *_ = play([ready()], [Reply(ready(), 10_001, waiting=True)], startup_ms=10_000)
    assert ending(record) == ("1-0", "startup_timeout")


def test_startup_deadline():
    _, _, black = play([Reply(ready(), 400), resign()], [ready()], startup_ms=500)
    startup_receive = next(event for event in black.events if event[0] == "receive")
    assert startup_receive == ("receive", (400 + 500) * NS_PER_MS)


def test_both_fail_to_start():
    record, white, black = play(
        [PlayerClosed("no interpreter")], [Reply(ready(), 20_000)], startup_ms=10_000
    )
    assert ending(record) == ("*", "startup_timeout")
    assert record.outcome.winner is None
    assert "no interpreter" in record.outcome.detail
    assert white.sent_types() == ["init"]
    assert black.sent_types() == ["init"]


@pytest.mark.parametrize(
    ("line", "code"),
    [
        (move("e2e4"), "unexpected_message"),
        (ready(v=2), "unsupported_version"),
        (ready(lang="rust"), "schema_violation"),
        (b"\xff", "invalid_json"),
    ],
)
def test_protocol_violation_at_startup(line, code):
    record, white, _ = play([line], [ready()])
    assert ending(record) == ("0-1", "protocol_violation")
    assert white.sent_types() == ["init", "error", "game_over"]
    assert error_codes(white) == [code]


def test_start_position_that_is_already_over():
    record, white, black = play([ready()], [ready()], start_fen="k7/8/1Q6/8/8/8/8/7K b - - 0 1")
    assert ending(record) == ("1/2-1/2", "stalemate")
    assert record.moves == []
    assert white.sent_types() == black.sent_types() == ["init", "game_over"]


def test_threefold_repetition():
    shuffle_white = [move("g1f3"), move("f3g1")] * 2
    shuffle_black = [move("g8f6"), move("f6g8")] * 2
    record, *_ = play([ready(), *shuffle_white], [ready(), *shuffle_black])
    assert ending(record) == ("1/2-1/2", "threefold_repetition")
    assert len(record.moves) == 8


def test_max_moves():
    record, *_ = play([ready(), move("e2e4")], [ready(), move("e7e5")], max_moves=1)
    assert ending(record) == ("1/2-1/2", "max_moves")


def test_on_move_sees_every_move():
    time = FakeTime()
    seen = []
    white = ScriptedPlayer("W", time, [ready(), *FOOLS_MATE_WHITE])
    black = ScriptedPlayer("B", time, [ready(), *FOOLS_MATE_BLACK])
    settings = MatchSettings(initial_time_ms=1000)
    record = Match(white, black, settings, now=time, on_move=seen.append).play()
    assert seen == record.moves


def test_a_match_is_played_once():
    time = FakeTime()
    white = ScriptedPlayer("W", time, [ready(), resign()])
    black = ScriptedPlayer("B", time, [ready()])
    match = Match(white, black, MatchSettings(initial_time_ms=1000), now=time)
    match.play()
    with pytest.raises(RuntimeError):
        match.play()


@pytest.mark.parametrize("name", ["", "x" * 65, None])
def test_player_names_are_checked(name):
    time = FakeTime()
    with pytest.raises(ValueError, match="name"):
        Match(
            ScriptedPlayer(name, time, []),
            ScriptedPlayer("B", time, []),
            MatchSettings(initial_time_ms=1000),
        )


def test_infrastructure_error_closes_both_players():
    time = FakeTime()
    white = ScriptedPlayer("W", time, [ready(), OSError("pipe broken")])
    black = ScriptedPlayer("B", time, [ready()])
    with pytest.raises(OSError, match="pipe broken"):
        Match(white, black, MatchSettings(initial_time_ms=1000), now=time).play()
    assert white.events[-1] == black.events[-1] == ("close",)


def test_poll_before_turn_uses_the_current_time():
    time = FakeTime()
    white = ScriptedPlayer("W", time, [Reply(ready(), 7), resign()])
    black = ScriptedPlayer("B", time, [ready()])
    Match(white, black, MatchSettings(initial_time_ms=1000), now=time).play()
    receives = [event[1] for event in white.events if event[0] == "receive"]
    assert receives[1] == 7 * NS_PER_MS
