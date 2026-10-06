"""Template bot for SchachBotManager: book moves from a data file, then a simple capture rule.

Replace choose_move with your own search. Start it with
    python bot.py         talks to a referee over stdin/stdout, as on the server
    python bot.py --tcp   connects to a waiting sbm-arena, e.g. from the debugger
"""

import random

import sbm

# Centipawns per piece type: PAWN, KNIGHT, BISHOP, ROOK, QUEEN, KING.
PIECE_VALUES = (100, 300, 300, 500, 900, 0)
MATE = 100_000


def piece_value(piece: int) -> int:
    # A piece is color * 6 + type, e.g. sbm.BLACK_QUEEN == 6 + sbm.QUEEN.
    return 0 if piece == sbm.NO_PIECE else PIECE_VALUES[piece % 6]


def position_key(board: sbm.Board) -> str:
    """The first four FEN fields: pieces, side to move, castling rights, en passant."""
    return " ".join(board.fen().split()[:4])


def load_book() -> dict[str, list[str]]:
    """Lines "position | uci uci ..." from data/book.txt; # starts a comment."""
    book = {}
    for line in sbm.load_data("book.txt").decode("utf-8").splitlines():
        if line.strip() and not line.startswith("#"):
            position, moves = line.split("|")
            book[position.strip()] = moves.split()
    return book


class TemplateBot(sbm.Bot):
    def on_game_start(self, info: sbm.GameInfo) -> None:
        # Runs within the start-up budget: the place to load data and build tables.
        self.random = random.Random()
        self.book = load_book()
        color = "White" if info.color == sbm.WHITE else "Black"
        sbm.Log.info(f"playing {color} against {info.opponent_name}")

    def choose_move(self, board: sbm.Board, clock: sbm.Clock) -> sbm.Move:
        book_moves = self.book.get(position_key(board), [])
        if book_moves:
            self.report(sbm.Info(text="book"))
            return board.parse_move(self.random.choice(book_moves))

        moves = board.legal_moves()
        scores = {move.uci(): self.score(board, move) for move in moves}
        best = max(scores.values())
        sbm.Log.debug(
            f"{len(moves)} moves, best score {best}, {clock.remaining_ms} ms left"
        )
        self.report(sbm.Info(depth=1, score_cp=best))
        return self.random.choice(
            [move for move in moves if scores[move.uci()] == best]
        )

    def score(self, board: sbm.Board, move: sbm.Move) -> int:
        """Value of the captured piece, minus the moved piece if it can be taken back."""
        gain = piece_value(board.piece_at(move.to_square()))
        moved = piece_value(board.piece_at(move.from_square()))
        board.make_move(move)
        if board.is_checkmate():
            gain = MATE
        elif board.is_attacked(move.to_square(), board.side_to_move()):
            gain -= moved
        board.undo_move()
        return gain

    def on_game_end(self, result: sbm.GameResult) -> None:
        sbm.Log.info(f"game over: {result.result} {result.termination}")


if __name__ == "__main__":
    sbm.run(TemplateBot)
