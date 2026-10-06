"""Messages from the referee to a bot (spec/protocol/v1): init, turn, error and game_over."""

from sbm.referee.bot_messages import PROTOCOL_VERSION, SUPPORTED_VERSIONS
from sbm.referee.settings import MatchSettings

COLOR_NAMES = ("white", "black")
MAX_ERROR_MESSAGE_LENGTH = 1024


def init(settings: MatchSettings, color: int, opponent_name: str) -> dict:
    return {
        "type": "init",
        "supported": list(SUPPORTED_VERSIONS),
        "game_id": settings.game_id,
        "color": COLOR_NAMES[color],
        "start_fen": settings.start_fen,
        "initial_time_ms": settings.initial_time_ms,
        "increment_ms": settings.increment_ms,
        "startup_ms": settings.startup_ms,
        "memory_limit_mib": settings.memory_limit_mib,
        "discipline": settings.discipline,
        "opponent_name": opponent_name,
    }


def turn(
    last_move: str | None, fen: str, ply: int, remaining_ms: int, opponent_remaining_ms: int
) -> dict:
    return {
        "type": "turn",
        "v": PROTOCOL_VERSION,
        "last_move": last_move,
        "fen": fen,
        "ply": ply,
        "remaining_ms": remaining_ms,
        "opponent_remaining_ms": opponent_remaining_ms,
    }


def error(code: str, message: str) -> dict:
    return {"type": "error", "code": code, "message": message[:MAX_ERROR_MESSAGE_LENGTH]}


def game_over(result: str, termination: str) -> dict:
    return {"type": "game_over", "result": result, "termination": termination}
