"""How a rated match moves the ratings of its two sides (E103)."""

START = 2500
BASE = 50
STEP = 20
MAX_WIN = 100
MIN_WIN = 1
MAX_DRAW = 50


def white_gain(white: int, black: int, result: str) -> int:
    """Points White wins (negative: loses); Black's rating moves by the same amount the other
    way. One point less per full 20 the winner is ahead, one more per full 20 behind."""
    steps = abs(white - black) // STEP
    if result == "1/2-1/2":
        gain = min(MAX_DRAW, steps)
        return gain if white < black else -gain
    winner, loser = (white, black) if result == "1-0" else (black, white)
    ahead = winner >= loser
    gain = max(MIN_WIN, BASE - steps) if ahead else min(MAX_WIN, BASE + steps)
    return gain if result == "1-0" else -gain
