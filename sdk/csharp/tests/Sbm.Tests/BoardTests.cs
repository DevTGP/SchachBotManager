namespace Sbm.Tests;

/// <summary>Rules of the binding for boards that the vectors do not cover (kern-c-schnittstelle.md).</summary>
public class BoardTests
{
    private const string Start = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1";

    [Fact]
    public void CopiesAreIndependent()
    {
        var board = new Board();
        board.MakeMove(board.ParseMove("e2e4"));
        var copy = board.Copy();
        copy.MakeMove(copy.ParseMove("e7e5"));
        Assert.Single(board.MoveHistory());
        Assert.Equal(2, copy.MoveHistory().Length);
        copy.UndoMove();
        Assert.Equal(board.Fen(), copy.Fen());
    }

    [Fact]
    public void TextForTheDebugger()
    {
        Assert.Equal($"Board.FromFen(\"{Start}\")", new Board().ToString());
        Assert.Contains("r n b q k b n r", new Board().ToText(), StringComparison.Ordinal);
    }

    [Fact]
    public void HistoryWithNullMove()
    {
        var board = new Board();
        Assert.Empty(board.MoveHistory());
        board.MakeMove(board.ParseMove("g1f3"));
        board.MakeNullMove();
        Assert.Equal([board.MoveHistory()[0], Move.NullMove], board.MoveHistory());
        board.UndoNullMove();
        board.UndoMove();
        Assert.Equal(Start, board.Fen());
    }

    [Fact]
    public void LongHistory()
    {
        var board = new Board();
        string[] cycle = ["g1f3", "g8f6", "f3g1", "f6g8"];
        for (var i = 0; i < 400; i++)
        {
            board.MakeMove(board.ParseMove(cycle[i % 4]));
        }
        Assert.Equal(400, board.MoveHistory().Length);
        Assert.True(board.IsRepetition(3));
    }

    [Fact]
    public void ManyBoards()
    {
        // The handles are released by the garbage collector; the core must not run out.
        for (var i = 0; i < 100_000; i++)
        {
            _ = new Board().Copy();
        }
        GC.Collect();
        GC.WaitForPendingFinalizers();
        Assert.Equal(20, new Board().LegalMoves().Length);
    }

    [Fact]
    public void Version() => Assert.Matches(@"^\d+\.\d+\.\d+", Sdk.Version);
}
