// Plays from the book while it can, then the first legal move.
using Sbm;

namespace Uploaded;

internal static class Opening
{
    public static Move FirstMove(Board board, string[] book)
    {
        var moves = board.LegalMoves();
        foreach (var move in moves)
        {
            if (book.Contains(move.Uci()))
            {
                return move;
            }
        }
        return moves[0];
    }
}
