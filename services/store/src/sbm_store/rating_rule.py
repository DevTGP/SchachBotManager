"""How a rated match moves the ratings of its two sides (E103); the numbers are settings (E154)."""

from dataclasses import dataclass


@dataclass(frozen=True)
class RatingRule:
    """start is the rating without rated matches; base the gain between equal ratings; per full
    step the winner is ahead it gains one point less, at least min_win, per full step behind
    one more, at most max_win; a draw moves the lower rating up one point per full step, at
    most max_draw."""

    start: int = 2500
    base: int = 50
    step: int = 20
    max_win: int = 100
    min_win: int = 1
    max_draw: int = 50


DEFAULT = RatingRule()


def white_gain(white: int, black: int, result: str, rule: RatingRule) -> int:
    """Points White wins (negative: loses); Black's rating moves by the same amount the other
    way."""
    steps = abs(white - black) // rule.step
    if result == "1/2-1/2":
        gain = min(rule.max_draw, steps)
        return gain if white < black else -gain
    winner, loser = (white, black) if result == "1-0" else (black, white)
    if winner >= loser:
        gain = max(rule.min_win, rule.base - steps)
        return gain if result == "1-0" else -gain
    gain = min(rule.max_win, rule.base + steps)
    return gain if result == "1-0" else -gain
