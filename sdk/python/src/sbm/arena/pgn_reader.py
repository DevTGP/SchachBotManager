"""Games from PGN text: the tags and the moves of the main line (E69).

Comments, variations, annotations (NAGs) and move numbers are skipped. A game ends with its
result; a game without one ends at the next tag or at the end of the text.
"""

import re
from dataclasses import dataclass, field

TOKEN = re.compile(
    r"""
    (?P<tag>\[\s*(?P<name>[A-Za-z0-9_]+)\s+"(?P<value>(?:[^"\\]|\\.)*)"\s*\])
    | \{[^}]*\}                         # comment
    | ;[^\n]*                           # comment to the end of the line
    | (?P<open>\() | (?P<close>\))      # variation
    | \$\d+                             # annotation
    | (?P<result>1-0|0-1|1/2-1/2|\*)
    | \d+\.+                            # move number
    | (?P<move>[^\s{}();\[\]$.]+)
    | (?P<other>\S)
    """,
    re.VERBOSE,
)


class PgnError(ValueError):
    """The text is not PGN."""


@dataclass
class PgnGame:
    tags: dict[str, str] = field(default_factory=dict)
    # SAN as written, e.g. "Nf3", "exd8=Q+" or "O-O!?".
    moves: list[str] = field(default_factory=list)


def read_games(text: str) -> list[PgnGame]:
    # Lines starting with % are escaped from PGN entirely.
    text = "\n".join(line for line in text.splitlines() if not line.startswith("%"))
    games: list[PgnGame] = []
    game, depth = PgnGame(), 0
    for match in TOKEN.finditer(text):
        kind = match.lastgroup
        if kind == "other":
            raise PgnError(f"unexpected {match.group()!r} at character {match.start()}")
        if kind == "open":
            depth += 1
        elif kind == "close":
            if depth == 0:
                raise PgnError(f"')' without '(' at character {match.start()}")
            depth -= 1
        elif depth > 0:
            continue
        elif kind == "tag":
            if game.moves:
                games.append(game)
                game = PgnGame()
            game.tags[match.group("name")] = re.sub(r"\\(.)", r"\1", match.group("value"))
        elif kind == "move":
            game.moves.append(match.group())
        elif kind == "result":
            games.append(game)
            game = PgnGame()
    if depth > 0:
        raise PgnError("a variation is not closed")
    if game.tags or game.moves:
        games.append(game)
    return games
