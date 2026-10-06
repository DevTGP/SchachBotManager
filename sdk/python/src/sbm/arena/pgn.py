"""A finished game as PGN, readable by common chess programs."""

from dataclasses import dataclass

from sbm.arena.time_control import format_time_control
from sbm.referee import STANDARD_FEN, MatchRecord, MatchSettings

LINE_WIDTH = 80

# The Termination tag knows only a few values; the exact code stays in the final comment.
PGN_TERMINATIONS = {
    "timeout": "time forfeit",
    "timeout_insufficient_material": "time forfeit",
    "startup_timeout": "time forfeit",
    "illegal_move": "rules infraction",
    "protocol_violation": "rules infraction",
    "crash": "abandoned",
    "memory_limit": "abandoned",
    "max_moves": "adjudication",
    "aborted": "unterminated",
}


@dataclass(frozen=True)
class GameInfo:
    """What a PGN needs beyond the record; date in the form 2026.10.06."""

    event: str
    site: str
    date: str
    round: int


def to_pgn(record: MatchRecord, settings: MatchSettings, game: GameInfo) -> str:
    outcome = record.outcome
    tags = [
        ("Event", game.event),
        ("Site", game.site),
        ("Date", game.date),
        ("Round", str(game.round)),
        ("White", record.white.name),
        ("Black", record.black.name),
        ("Result", outcome.result),
    ]
    if record.start_fen != STANDARD_FEN:
        tags += [("SetUp", "1"), ("FEN", record.start_fen)]
    clock = settings.clock
    time_control = format_time_control(settings.initial_time_ms, settings.increment_ms)
    tags += [
        ("TimeControl", time_control if clock else "-"),
        ("Termination", PGN_TERMINATIONS.get(outcome.termination, "normal")),
    ]
    header = "".join(f'[{name} "{_escape(value)}"]\n' for name, value in tags)
    return f"{header}\n{_wrap(_movetext(record))}\n"


def _escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def _movetext(record: MatchRecord) -> list[str]:
    fields = record.start_fen.split()
    black_first = fields[1] == "b"
    number = int(fields[5])
    tokens = []
    for index, move in enumerate(record.moves):
        white_to_move = (index % 2 == 0) != black_first
        if white_to_move:
            tokens.append(f"{number}.")
        elif index == 0:
            tokens.append(f"{number}...")
        tokens.append(move.san)
        if not white_to_move:
            number += 1
    outcome = record.outcome
    comment = f"{outcome.termination}: {outcome.detail}"
    comment = " ".join(comment.replace("}", ")").split())
    tokens += ["{" + comment + "}", outcome.result]
    return tokens


def _wrap(tokens: list[str]) -> str:
    """Joins tokens with spaces in lines of at most LINE_WIDTH characters; comments may break."""
    words = [word for token in tokens for word in token.split()]
    lines, line = [], ""
    for word in words:
        if line and len(line) + 1 + len(word) > LINE_WIDTH:
            lines.append(line)
            line = word
        else:
            line = f"{line} {word}" if line else word
    lines.append(line)
    return "\n".join(lines)
