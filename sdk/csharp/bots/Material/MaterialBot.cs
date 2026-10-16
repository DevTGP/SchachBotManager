using System.Numerics;

namespace Sbm.Bots;

/// <summary>
/// Counts material two half-moves ahead: alpha-beta search over its own move and the reply.
/// It neither hangs a piece to a direct capture nor misses a mate in one, and picks at random
/// among equally good moves. A template for a bot with search: MakeMove and UndoMove on the
/// board, an evaluation on raw data (bitboards) and search information with Report.
/// Port of sbm.bots.material in the Python SDK.
/// </summary>
internal sealed class MaterialBot : Bot
{
    internal const int Depth = 2;
    internal const int Mate = 100_000;

    // Scores beyond this are mates; the distance in half-moves is Mate minus the score.
    private const int MateBound = Mate - 1_000;

    // Centipawns per piece type, in the order Pawn, Knight, Bishop, Rook, Queen; the king counts 0.
    private static readonly int[] PieceValues = [100, 300, 300, 500, 900, 0];

    private readonly Random _random = new();
    private long _nodes;

    public override Move ChooseMove(Board board, Clock clock)
    {
        _nodes = 0;
        var bestScore = -Mate - 1;
        var bestMoves = new List<Move>();
        foreach (var move in board.LegalMoves())
        {
            board.MakeMove(move);
            // A window just below the best score keeps equally good moves exact.
            var score = -Search(board, Depth - 1, -Mate - 1, -(bestScore - 1), 1);
            board.UndoMove();
            if (score > bestScore)
            {
                bestScore = score;
                bestMoves.Clear();
                bestMoves.Add(move);
            }
            else if (score == bestScore)
            {
                bestMoves.Add(move);
            }
        }
        Report(SearchInfo(bestScore));
        return bestMoves[_random.Next(bestMoves.Count)];
    }

    /// <summary>Material of the side to move minus that of the opponent, in centipawns.</summary>
    internal static int Material(Board board)
    {
        var bitboards = board.Bitboards();
        var white = 0;
        var black = 0;
        for (var piece = 0; piece < PieceValues.Length; piece++)
        {
            white += PieceValues[piece] * BitOperations.PopCount(bitboards[piece]);
            black += PieceValues[piece] * BitOperations.PopCount(bitboards[6 + piece]);
        }
        return board.SideToMove() == Color.White ? white - black : black - white;
    }

    /// <summary>Negamax score of the side to move; ply counts half-moves from the root.</summary>
    private int Search(Board board, int depth, int alpha, int beta, int ply)
    {
        _nodes++;
        if (board.IsCheckmate())
        {
            return -Mate + ply; // a mate further away is less bad
        }
        if (board.IsDraw())
        {
            return 0;
        }
        if (depth == 0)
        {
            return Material(board);
        }
        foreach (var move in board.LegalMoves())
        {
            board.MakeMove(move);
            var score = -Search(board, depth - 1, -beta, -alpha, ply + 1);
            board.UndoMove();
            if (score >= beta)
            {
                return beta;
            }
            alpha = Math.Max(alpha, score);
        }
        return alpha;
    }

    private Info SearchInfo(int score) =>
        score switch
        {
            > MateBound => new Info
            {
                Depth = Depth,
                ScoreMate = (Mate - score + 1) / 2,
                Nodes = _nodes,
            },
            < -MateBound => new Info
            {
                Depth = Depth,
                ScoreMate = -((Mate + score) / 2),
                Nodes = _nodes,
            },
            _ => new Info
            {
                Depth = Depth,
                ScoreCp = score,
                Nodes = _nodes,
            },
        };
}
