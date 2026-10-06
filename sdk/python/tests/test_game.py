"""One game against a scripted referee: init, turns, game_over and the bot's answers."""

import io
import json

import pytest
from protocol_schemas import example, examples, violations

import sbm
from sbm import protocol
from sbm.channel import Channel, ProtocolError
from sbm.game import BotError, Game

START = example("turn.first_move")["fen"]
GAME_OVER = example("game_over.checkmate")


class FirstMove(sbm.Bot):
    """Plays the first legal move and records what the SDK passes in."""

    def __init__(self):
        self.calls = []

    def on_game_start(self, info):
        self.calls.append(("start", info))

    def choose_move(self, board, clock):
        self.calls.append(("turn", board.fen(), clock))
        return board.legal_moves()[0]

    def on_game_end(self, result):
        self.calls.append(("end", result))


def play(bot: sbm.Bot, *messages: dict) -> list[dict]:
    """Plays the messages to the bot and returns its answers, each checked against the schema."""
    data = "".join(json.dumps(message) + "\n" for message in messages).encode()
    writer = io.BytesIO()
    Game(bot, Channel(io.BytesIO(data), writer)).play()
    answers = [json.loads(line) for line in writer.getvalue().splitlines()]
    for answer in answers:
        assert violations("bot_message", answer) == []
    return answers


def turn(fen: str, ply: int, last_move: str | None = None, remaining_ms: int = 1000) -> dict:
    return {
        "type": "turn",
        "v": 1,
        "last_move": last_move,
        "fen": fen,
        "ply": ply,
        "remaining_ms": remaining_ms,
        "opponent_remaining_ms": 2000,
    }


def test_white_game(capsys):
    bot = FirstMove()
    answers = play(bot, example("init.standard"), example("turn.first_move"), GAME_OVER)
    assert answers[0] == {"type": "ready", "v": 1, "sdk": sbm.core_version(), "lang": "python"}
    assert answers[1] == {"type": "move", "v": 1, "move": sbm.Board().legal_moves()[0].uci()}
    assert len(answers) == 2
    (_, info), (_, fen, clock), (_, result) = bot.calls
    assert info == sbm.GameInfo(
        game_id="66f1c2a9e4b0a1b2c3d4e5f6",
        color=sbm.WHITE,
        opponent_name="Stockfisch Junior",
        start_fen=START,
        initial_time_ms=300000,
        increment_ms=2000,
        startup_ms=10000,
        memory_limit_mib=1024,
        discipline="Blitz 5+2",
    )
    assert fen == START
    assert clock.remaining_ms() == 300000
    assert clock.opponent_remaining_ms() == 300000
    assert clock.increment_ms() == 2000
    assert result == sbm.GameResult(result="0-1", termination="checkmate")
    assert capsys.readouterr().err == ""


def test_black_follows_the_opponent_moves(capsys):
    bot = FirstMove()
    start = example("init.black_custom_position")
    promotion = example("turn.after_promotion")
    king = sbm.Board.from_fen(promotion["fen"])
    king.make_move(king.legal_moves()[0])
    after = king.copy()
    reply = after.legal_moves()[-1]
    after.make_move(reply)
    later = turn(after.fen(), 121, reply.uci())
    answers = play(bot, start, promotion, later, GAME_OVER)
    assert [answer["type"] for answer in answers] == ["ready", "move", "move"]
    assert bot.calls[1][1] == promotion["fen"]
    assert bot.calls[2][1] == after.fen()
    assert capsys.readouterr().err == ""


def test_en_passant_square_without_capture_is_no_mismatch(capsys):
    black = dict(example("init.standard"), color="black")
    play(FirstMove(), black, example("turn.after_opponent_move"), GAME_OVER)
    assert capsys.readouterr().err == ""


def test_mismatch_adopts_the_referee_position(capsys):
    bot = FirstMove()
    other = "rnbqkbnr/pppppppp/8/8/3P4/8/PPP1PPPP/RNBQKBNR b KQkq - 0 1"
    black = dict(example("init.standard"), color="black")
    play(bot, black, turn(other, 1, "e2e4"), GAME_OVER)
    assert bot.calls[1][1] == other
    assert "WARN  own position differs" in capsys.readouterr().err


def test_unparsable_last_move_is_repaired_by_the_fen(capsys):
    bot = FirstMove()
    fen = example("turn.after_opponent_move")["fen"]
    play(bot, dict(example("init.standard"), color="black"), turn(fen, 1, "e2e5"), GAME_OVER)
    assert "WARN  own position differs" in capsys.readouterr().err


def test_bot_changes_to_its_board_stay_local():
    class Mutating(FirstMove):
        def choose_move(self, board, clock):
            move = super().choose_move(board, clock)
            board.make_move(board.legal_moves()[0])
            board.make_move(board.legal_moves()[0])
            return move

    bot = Mutating()
    first = sbm.Board()
    first.make_move(first.legal_moves()[0])
    reply = first.legal_moves()[0]
    first.make_move(reply)
    play(
        bot, example("init.standard"), turn(START, 0), turn(first.fen(), 2, reply.uci()), GAME_OVER
    )
    assert bot.calls[2][1] == first.fen()


def test_resign():
    class Resigning(FirstMove):
        def choose_move(self, board, clock):
            return sbm.RESIGN

    answers = play(Resigning(), example("init.standard"), turn(START, 0), GAME_OVER)
    assert answers[1] == {"type": "resign", "v": 1}


def test_report_belongs_to_one_turn():
    class Reporting(FirstMove):
        def choose_move(self, board, clock):
            if board.fullmove_number() == 1:
                self.report(sbm.Info(depth=3, text="first"))
            return super().choose_move(board, clock)

    second = sbm.Board.from_fen("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 2")
    answers = play(
        Reporting(),
        example("init.standard"),
        turn(START, 0),
        turn(second.fen(), 2),
        GAME_OVER,
    )
    assert answers[1]["info"] == {"depth": 3, "text": "first"}
    assert "info" not in answers[2]


def test_report_before_the_turn_is_dropped():
    class Early(FirstMove):
        def on_game_start(self, info):
            self.report(sbm.Info(depth=1))

    answers = play(Early(), example("init.standard"), turn(START, 0), GAME_OVER)
    assert "info" not in answers[1]


def test_report_needs_an_info():
    with pytest.raises(TypeError, match="Info"):
        FirstMove().report({"depth": 1})


@pytest.mark.parametrize(
    ("answer", "message"),
    [
        (None, "returned NoneType"),
        ("e2e4", "returned str"),
        (sbm.NULL_MOVE, "no UCI form"),
    ],
)
def test_unusable_answers(answer, message):
    class Wrong(FirstMove):
        def choose_move(self, board, clock):
            return answer

    with pytest.raises(BotError, match=message):
        play(Wrong(), example("init.standard"), turn(START, 0), GAME_OVER)


@pytest.mark.parametrize("callback", ["on_game_start", "choose_move", "on_game_end"])
def test_exceptions_in_callbacks(callback):
    def fail(*args):
        raise RuntimeError("boom")

    bot = FirstMove()
    setattr(bot, callback, fail)
    with pytest.raises(BotError, match=f"{callback} raised RuntimeError: boom") as caught:
        play(bot, example("init.standard"), turn(START, 0), GAME_OVER)
    assert isinstance(caught.value.__cause__, RuntimeError)


def test_illegal_own_move_is_left_to_the_referee(capsys):
    class Illegal(FirstMove):
        def choose_move(self, board, clock):
            return sbm.Move.parse("e2e5")

    answers = play(Illegal(), example("init.standard"), turn(START, 0), GAME_OVER)
    assert answers[1]["move"] == "e2e5"
    assert "WARN  own move e2e5 is not legal" in capsys.readouterr().err


def test_unknown_types_and_fields_are_ignored(capsys):
    init = dict(example("init.standard"), future_field={"x": 1})
    answers = play(
        FirstMove(), init, {"type": "ping"}, dict(turn(START, 0), hint="e2e4"), GAME_OVER
    )
    assert [answer["type"] for answer in answers] == ["ready", "move"]
    assert "WARN  ignoring a message of unknown type 'ping'" in capsys.readouterr().err


def test_referee_errors_are_logged(capsys):
    play(FirstMove(), example("init.standard"), example("error.illegal_move"), GAME_OVER)
    assert "ERROR referee reports illegal_move: e1g1: castling through check" in (
        capsys.readouterr().err
    )


def test_unsupported_version_still_answers_ready(capsys):
    init = dict(example("init.standard"), supported=[2])
    answers = play(FirstMove(), init, GAME_OVER)
    assert answers[0]["type"] == "ready"
    assert "ERROR the referee supports protocol versions [2]" in capsys.readouterr().err


def test_end_of_input_before_game_over(capsys):
    play(FirstMove(), example("init.standard"), turn(START, 0))
    assert "WARN  input ended before game_over" in capsys.readouterr().err


def test_ply_appears_in_log_lines(capsys):
    class Logging(FirstMove):
        def choose_move(self, board, clock):
            sbm.Log.info("thinking")
            return super().choose_move(board, clock)

    play(Logging(), example("init.standard"), turn(START, 0), GAME_OVER)
    assert "[ply 0] INFO  thinking" in capsys.readouterr().err


@pytest.mark.parametrize(
    "messages",
    [
        [turn(START, 0)],
        [example("init.standard"), example("init.standard")],
        [dict(example("init.standard"), color="red")],
        [dict(example("init.standard"), start_fen="no fen")],
        [dict(example("init.standard"), increment_ms=True)],
        [example("init.standard"), dict(turn(START, 0), fen="8/8/8/8/8/8/8/8 w - - 0 1")],
        [example("init.standard"), dict(turn(START, 0), remaining_ms="1000")],
        [example("init.standard"), {"type": "game_over", "result": "1-0"}],
    ],
)
def test_protocol_errors(messages):
    with pytest.raises(ProtocolError):
        play(FirstMove(), *messages)


@pytest.mark.parametrize("path", examples("init"), ids=lambda path: path.stem)
def test_all_init_examples(path):
    init = json.loads(path.read_text("utf-8"))
    info = protocol.game_info(init)
    assert info.start_fen == init["start_fen"]
    assert protocol.PROTOCOL_VERSION in protocol.supported_versions(init)


@pytest.mark.parametrize("path", examples("game_over"), ids=lambda path: path.stem)
def test_all_game_over_examples(path):
    game_over = json.loads(path.read_text("utf-8"))
    result = protocol.game_result(game_over)
    assert (result.result, result.termination) == (game_over["result"], game_over["termination"])
