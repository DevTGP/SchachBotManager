using Sbm;

namespace MyBot;

/// <summary>Template bot: book moves from a data file, then a simple capture rule.</summary>
/// <remarks>Replace ChooseMove with your own search.</remarks>
public sealed class TemplateBot : Bot
{
    // Centipawns per piece type: Pawn, Knight, Bishop, Rook, Queen, King.
    private static readonly int[] PieceValues = [100, 300, 300, 500, 900, 0];
    private const int Mate = 100_000;

    private readonly Random _random = new();
    private Dictionary<string, string[]> _book = [];

    public override void OnGameStart(GameInfo info)
    {
        // Runs within the start-up budget: the place to load data and build tables.
        _book = LoadBook();
        var color = info.Color == Color.White ? "White" : "Black";
        Log.Info($"playing {color} against {info.OpponentName}");
    }

    public override Move ChooseMove(Board board, Clock clock)
    {
        if (_book.TryGetValue(PositionKey(board), out var bookMoves))
        {
            Report(new Info { Text = "book" });
            return board.ParseMove(bookMoves[_random.Next(bookMoves.Length)]);
        }

        var moves = board.LegalMoves();
        var scores = moves.Select(move => Score(board, move)).ToArray();
        var best = scores.Max();
        Log.Debug($"{moves.Length} moves, best score {best}, {clock.RemainingMs()} ms left");
        Report(new Info { Depth = 1, ScoreCp = best });
        var bestMoves = moves.Where((_, index) => scores[index] == best).ToArray();
        return bestMoves[_random.Next(bestMoves.Length)];
    }

    public override void OnGameEnd(GameResult result) =>
        Log.Info($"game over: {result.Result} {result.Termination}");

    /// <summary>Value of the captured piece, minus the moved piece if it can be taken back.</summary>
    private static int Score(Board board, Move move)
    {
        var gain = PieceValue(board.PieceAt(move.ToSquare()));
        var moved = PieceValue(board.PieceAt(move.FromSquare()));
        board.MakeMove(move);
        if (board.IsCheckmate())
        {
            gain = Mate;
        }
        else if (board.IsAttacked(move.ToSquare(), board.SideToMove()))
        {
            gain -= moved;
        }
        board.UndoMove();
        return gain;
    }

    // A piece is color * 6 + type, e.g. Piece.BlackQueen == 6 + PieceType.Queen.
    private static int PieceValue(byte piece) =>
        piece == Piece.NoPiece ? 0 : PieceValues[piece % 6];

    /// <summary>The first four FEN fields: pieces, side to move, castling rights, en passant.</summary>
    private static string PositionKey(Board board) =>
        string.Join(' ', board.Fen().Split(' ').Take(4));

    /// <summary>Lines "position | uci uci ..." from data/book.txt; # starts a comment.</summary>
    private static Dictionary<string, string[]> LoadBook()
    {
        var book = new Dictionary<string, string[]>();
        var text = System.Text.Encoding.UTF8.GetString(Sdk.LoadData("book.txt"));
        foreach (var line in text.Split('\n'))
        {
            if (string.IsNullOrWhiteSpace(line) || line.StartsWith('#'))
            {
                continue;
            }
            var parts = line.Split('|');
            book[parts[0].Trim()] = parts[1].Split(' ', StringSplitOptions.RemoveEmptyEntries);
        }
        return book;
    }
}
