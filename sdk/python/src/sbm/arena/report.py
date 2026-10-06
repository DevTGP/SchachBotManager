"""What the arena prints on stdout: games, moves on request, results and the score."""

from typing import TextIO

from sbm.arena.series import Game, Score
from sbm.referee import MatchRecord, MoveRecord


class ConsoleReport:
    def __init__(self, out: TextIO, start_fen: str, games: int) -> None:
        self._out = out
        fields = start_fen.split()
        self._black_first = fields[1] == "b"
        self._first_number = int(fields[5])
        self._games = games

    def _print(self, text: str) -> None:
        print(text, file=self._out, flush=True)

    def start(self, game: Game) -> None:
        self._print(
            f"Game {game.number}/{self._games}: {game.white} (White) vs {game.black} (Black)"
        )

    def move(self, move: MoveRecord) -> None:
        self._print(f"  {self.move_label(move):<14} {_seconds(move.elapsed_ms):>9}{_info(move)}")

    def move_label(self, move: MoveRecord) -> str:
        """The move with its number, e.g. "12. Nf3" or "12... Nf6"."""
        index = move.ply - 1 + self._black_first
        number = self._first_number + index // 2
        return f"{number}{'.' if index % 2 == 0 else '...'} {move.san}"

    def end(self, game: Game, record: MatchRecord) -> None:
        outcome = record.outcome
        self._print(f"  {outcome.result} {outcome.termination}: {outcome.detail}")

    def scores(self, scores: dict[str, Score]) -> None:
        width = max(len("Bot"), *(len(name) for name in scores))
        self._print(f"\n{'Bot':<{width}}  Points  Won  Drawn  Lost  Unfinished")
        for name, score in sorted(scores.items(), key=lambda item: -item[1].points):
            self._print(
                f"{name:<{width}}  {score.points:>6g}  {score.wins:>3}  {score.draws:>5}"
                f"  {score.losses:>4}  {score.unfinished:>10}"
            )


def _seconds(milliseconds: int) -> str:
    return f"{milliseconds / 1000:.3f} s"


def _info(move: MoveRecord) -> str:
    info = move.info or {}
    parts = []
    if "depth" in info:
        parts.append(f"depth {info['depth']}")
    if "score_cp" in info:
        parts.append(f"score {info['score_cp'] / 100:+.2f}")
    if "score_mate" in info:
        parts.append(f"mate {info['score_mate']}")
    if "text" in info:
        parts.append(" ".join(info["text"].split()))
    return "  " + ", ".join(parts) if parts else ""
