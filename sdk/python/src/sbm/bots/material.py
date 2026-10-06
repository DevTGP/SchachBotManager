"""Counts material two half-moves ahead: alpha-beta search over its own move and the reply.

It neither hangs a piece to a direct capture nor misses a mate in one, and picks at random
among equally good moves. A template for a bot with search: make_move and undo_move on the
board, an evaluation on raw data (bitboards) and search information with report.
"""

import random

import sbm

DEPTH = 2
# Centipawns per piece type, in the order PAWN, KNIGHT, BISHOP, ROOK, QUEEN; the king counts 0.
PIECE_VALUES = (100, 300, 300, 500, 900, 0)
MATE = 100_000
# Scores beyond this are mates; the distance in half-moves is MATE minus the score.
MATE_BOUND = MATE - 1_000


def material(board: sbm.Board) -> int:
    """Material of the side to move minus that of the opponent, in centipawns."""
    bitboards = board.bitboards()
    white = sum(value * bitboards[piece].bit_count() for piece, value in enumerate(PIECE_VALUES))
    black = sum(
        value * bitboards[6 + piece].bit_count() for piece, value in enumerate(PIECE_VALUES)
    )
    return white - black if board.side_to_move() == sbm.WHITE else black - white


class MaterialBot(sbm.Bot):
    def __init__(self) -> None:
        self.random = random.Random()
        self.nodes = 0

    def choose_move(self, board: sbm.Board, clock: sbm.Clock) -> sbm.Move:
        self.nodes = 0
        best_score, best_moves = -MATE - 1, []
        for move in board.legal_moves():
            board.make_move(move)
            # A window just below the best score keeps equally good moves exact.
            score = -self.search(board, DEPTH - 1, -MATE - 1, -(best_score - 1), 1)
            board.undo_move()
            if score > best_score:
                best_score, best_moves = score, [move]
            elif score == best_score:
                best_moves.append(move)
        self.report(self.info(best_score))
        return self.random.choice(best_moves)

    def search(self, board: sbm.Board, depth: int, alpha: int, beta: int, ply: int) -> int:
        """Negamax score of the side to move; ply counts half-moves from the root."""
        self.nodes += 1
        if board.is_checkmate():
            return -MATE + ply  # a mate further away is less bad
        if board.is_draw():
            return 0
        if depth == 0:
            return material(board)
        for move in board.legal_moves():
            board.make_move(move)
            score = -self.search(board, depth - 1, -beta, -alpha, ply + 1)
            board.undo_move()
            if score >= beta:
                return beta
            alpha = max(alpha, score)
        return alpha

    def info(self, score: int) -> sbm.Info:
        if score > MATE_BOUND:
            return sbm.Info(depth=DEPTH, score_mate=(MATE - score + 1) // 2, nodes=self.nodes)
        if score < -MATE_BOUND:
            return sbm.Info(depth=DEPTH, score_mate=-((MATE + score) // 2), nodes=self.nodes)
        return sbm.Info(depth=DEPTH, score_cp=score, nodes=self.nodes)


if __name__ == "__main__":
    sbm.run(MaterialBot)
