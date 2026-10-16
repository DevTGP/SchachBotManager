using Sbm.Bots;

namespace Sbm.Tests.Bots;

/// <summary>The reference bot Material on the positions of the Python SDK's tests.</summary>
public sealed class MaterialBotTests
{
    private static readonly Clock Clock = new(60_000, 60_000, 0);

    [Fact]
    public void MaterialCountsForTheSideToMove()
    {
        Assert.Equal(0, MaterialBot.Material(new Board()));
        Assert.Equal(1400, MaterialBot.Material(Board.FromFen("4k3/8/8/8/8/8/8/R3K2Q w - - 0 1")));
        Assert.Equal(-1400, MaterialBot.Material(Board.FromFen("4k3/8/8/8/8/8/8/R3K2Q b - - 0 1")));
    }

    [Fact]
    public void TakesAHangingQueen()
    {
        var (uci, info) = Choose(new MaterialBot(), "4k3/8/8/3q4/8/8/8/3RK3 w - - 0 1");
        Assert.Equal("d1d5", uci);
        Assert.Equal((2, 500), (info.Depth, info.ScoreCp));
        Assert.True(info.Nodes > 0);
    }

    [Fact]
    public void DoesNotTakeADefendedPawnWithTheQueen()
    {
        for (var run = 0; run < 10; run++)
        {
            var (uci, info) = Choose(new MaterialBot(), "4k3/8/2p5/3p4/8/8/8/3QK3 w - - 0 1");
            Assert.NotEqual("d1d5", uci);
            Assert.Equal(700, info.ScoreCp); // queen against two pawns
        }
    }

    [Fact]
    public void MatesInOne()
    {
        var (uci, info) = Choose(new MaterialBot(), "6k1/5ppp/8/8/8/8/8/R5K1 w - - 0 1");
        Assert.Equal("a1a8", uci);
        Assert.Equal(1, info.ScoreMate);
        Assert.Null(info.ScoreCp);
    }

    [Fact]
    public void AvoidsAMateInOne()
    {
        // Nb3 allows Re1#; Nc2 guards e1, pawn and king moves make room for the king.
        for (var run = 0; run < 10; run++)
        {
            var (uci, info) = Choose(new MaterialBot(), "4r1k1/5ppp/8/8/8/8/5PPP/N5K1 w - - 0 1");
            Assert.NotEqual("a1b3", uci);
            Assert.Equal(300 - 500, info.ScoreCp);
        }
    }

    [Fact]
    public void EqualMovesAreChosenAtRandom()
    {
        var start = new Board().Fen();
        var moves = Enumerable
            .Range(0, 30)
            .Select(_ => Choose(new MaterialBot(), start).Uci)
            .ToHashSet();
        Assert.True(moves.Count > 5);
    }

    private static (string Uci, Info Info) Choose(MaterialBot bot, string fen)
    {
        var board = Board.FromFen(fen);
        var move = bot.ChooseMove(board, Clock);
        Assert.Equal(fen, board.Fen()); // every searched move is undone
        Assert.True(board.IsLegal(move));
        var info = bot.TakeReport();
        Assert.NotNull(info);
        return (move.Uci(), info);
    }
}
