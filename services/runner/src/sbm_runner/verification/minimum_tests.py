"""The Mindesttests of an uploaded bot: games against the jailed random bot (verifikation.md, E92).

There are no fixed seeds; a bot that plays by the rules passes whatever the random bot does.
"""

from dataclasses import dataclass

from sbm import BLACK, WHITE
from sbm.referee import STANDARD_FEN, Match, MatchRecord, MatchSettings, Outcome, Player
from sbm_store.bots import BUILTIN_PREFIX

from sbm_runner.sandbox.jail_player import GRACE_SECONDS

RANDOM = {"_id": "random", "name": "Random", "source_ref": f"{BUILTIN_PREFIX}random_mover"}
COLOR_NAMES = ("white", "black")
DISCIPLINE = "Verification"
# Endings that fail a test unless the bot's own color won.
FAILURES = frozenset(
    {
        "timeout",
        "timeout_insufficient_material",
        "illegal_move",
        "protocol_violation",
        "crash",
        "memory_limit",
        "startup_timeout",
        "aborted",
    }
)
MAX_STDERR_BYTES = 1024 * 1024

# One move from positions with a special rule; the bot has the side to move.
POSITIONS = {
    "opening": STANDARD_FEN,
    "check": "rnbqkbnr/ppp2ppp/8/1B1pp3/4P3/8/PPPP1PPP/RNBQK1NR b KQkq - 1 3",
    "promotion": "8/1P6/8/8/8/8/2k4r/K7 w - - 0 1",
    "en_passant": "rnbqkbnr/ppp1p1pp/8/3pPp2/8/8/PPPP1PPP/RNBQKBNR w KQkq f6 0 3",
    "only_move": "7k/8/8/8/8/8/8/K5R1 b - - 0 1",
}


@dataclass(frozen=True)
class TestGame:
    name: str
    color: int
    settings: MatchSettings


def _settings(name: str, **values) -> MatchSettings:
    return MatchSettings(game_id=f"verify-{name}", discipline=DISCIPLINE, **values)


def _position(name: str, fen: str) -> TestGame:
    color = WHITE if fen.split()[1] == "w" else BLACK
    settings = _settings(name, initial_time_ms=5_000, max_moves=1, start_fen=fen)
    return TestGame(f"position_{name}", color, settings)


TEST_GAMES = (
    *(_position(name, fen) for name, fen in POSITIONS.items()),
    TestGame(
        "game_white",
        WHITE,
        _settings("game_white", initial_time_ms=10_000, increment_ms=100, max_moves=150),
    ),
    TestGame(
        "game_black",
        BLACK,
        _settings("game_black", initial_time_ms=10_000, increment_ms=100, max_moves=150),
    ),
    TestGame(
        "time_pressure", WHITE, _settings("time_pressure", initial_time_ms=2_000, max_moves=20)
    ),
)


def play_test(game: TestGame, bot: Player, opponent: Player) -> dict:
    """Plays one test game; bot must be a JailPlayer, which tells how it ended after close."""
    players = (bot, opponent) if game.color == WHITE else (opponent, bot)
    record = Match(*players, game.settings).play()
    outcome = record.outcome
    problem = _problem(game.color, record, bot)
    return {
        "name": game.name,
        "color": COLOR_NAMES[game.color],
        "result": outcome.result,
        "termination": outcome.termination,
        "detail": outcome.detail,
        "plies": len(record.moves),
        "passed": problem is None,
        "problem": problem,
    }


def _problem(color: int, record: MatchRecord, bot: Player) -> str | None:
    outcome = record.outcome
    if _at_fault(color, outcome, record):
        return f"{outcome.termination}: {outcome.detail}"
    if not bot.exited_cleanly:
        return f"did not exit with code 0 within {GRACE_SECONDS:g} s after game_over"
    if bot.stderr_bytes > MAX_STDERR_BYTES:
        return f"wrote {bot.stderr_bytes} bytes to stderr, more than {MAX_STDERR_BYTES}"
    return None


def _at_fault(color: int, outcome: Outcome, record: MatchRecord) -> bool:
    if outcome.termination not in FAILURES:
        return False
    if outcome.winner is not None:
        return outcome.winner != color
    if outcome.termination == "timeout_insufficient_material":
        # The side that ran out of time is the one to move at the end.
        fen = record.moves[-1].fen if record.moves else record.start_fen
        return (WHITE if fen.split()[1] == "w" else BLACK) == color
    return True
