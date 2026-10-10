"""The messages the SDK writes to the viewer (spec/protocol/viewer-v1/)."""

from sbm.constants import DEBUG, ERROR, INFO, TRACE, WARN
from sbm.records import GameInfo

VIEWER_VERSION = 1
MAX_NAME_LENGTH = 64
MAX_LOG_LENGTH = 4096

LOG_LEVELS = {TRACE: "debug", DEBUG: "debug", INFO: "info", WARN: "warn", ERROR: "error"}


def start(bot: str, info: GameInfo) -> dict:
    message = {
        "type": "start",
        "v": VIEWER_VERSION,
        "bot": bot[:MAX_NAME_LENGTH] or "Bot",
        "color": "white" if info.color == 0 else "black",
        "opponent": info.opponent_name,
        "start_fen": info.start_fen,
        "initial_time_ms": info.initial_time_ms,
        "increment_ms": info.increment_ms,
    }
    if info.discipline:
        message["discipline"] = info.discipline
    return message


def move(
    ply: int,
    uci: str,
    fen: str,
    by_bot: bool,
    clocks: tuple[int, int] | None,
    elapsed_ms: int | None = None,
    info: dict | None = None,
) -> dict:
    """clocks: remaining times of white and black after the move, if the SDK knows them."""
    message = {
        "type": "move",
        "ply": ply,
        "move": uci,
        "fen": fen,
        "by": "bot" if by_bot else "opponent",
    }
    if clocks is not None:
        message["white_ms"], message["black_ms"] = (max(0, ms) for ms in clocks)
    if elapsed_ms is not None:
        message["elapsed_ms"] = max(0, elapsed_ms)
    if info:
        message["info"] = info
    return message


def log(level: int, time: str, text: str) -> dict:
    return {"type": "log", "level": LOG_LEVELS[level], "text": text[:MAX_LOG_LENGTH], "time": time}
