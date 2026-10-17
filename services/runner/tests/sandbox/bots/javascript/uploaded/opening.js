// Plays from the book while it can, then the first legal move.
export function firstMove(board, book) {
  const moves = board.legalMoves();
  return moves.find((move) => book.includes(move.uci())) ?? moves[0];
}
