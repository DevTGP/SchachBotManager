"""Plays from the book while it can, then the first legal move."""

import sbm


def first_move(board: sbm.Board, book: list[str]) -> sbm.Move:
    moves = board.legal_moves()
    for move in moves:
        if move.uci() in book:
            return move
    return moves[0]
