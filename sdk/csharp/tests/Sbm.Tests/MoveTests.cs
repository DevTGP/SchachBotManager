namespace Sbm.Tests;

/// <summary>Move as value type: equality, text and the special moves.</summary>
public class MoveTests
{
    [Fact]
    public void EqualByValue()
    {
        var parsed = Move.Parse("e2e4");
        var built = new Move(Square.E2, Square.E4, MoveFlags.Quiet);
        Assert.Equal(parsed, built);
        Assert.True(parsed == built);
        Assert.False(parsed != built);
        Assert.Equal(parsed.GetHashCode(), built.GetHashCode());
        Assert.NotEqual(parsed, new Move(Square.E2, Square.E4, MoveFlags.DoublePawnPush));
        Assert.False(parsed.Equals("e2e4"));
    }

    [Fact]
    public void DefaultIsNullMove() => Assert.Equal(Move.NullMove, default);

    [Fact]
    public void Text()
    {
        Assert.Equal(
            "<Move e2e4 flags=1>",
            new Move(Square.E2, Square.E4, MoveFlags.DoublePawnPush).ToString()
        );
        Assert.Equal(
            "<Move e7e8q flags=11>",
            new Move(Square.E7, Square.E8, MoveFlags.PromotionQueen).ToString()
        );
        Assert.Equal("<Move NullMove>", Move.NullMove.ToString());
        Assert.Equal("<Move Resign>", Move.Resign.ToString());
    }

    [Fact]
    public void SpecialMovesHaveNoUci()
    {
        Assert.Throws<InvalidArgumentException>(() => Move.NullMove.Uci());
        Assert.Throws<InvalidArgumentException>(() => Move.Resign.Uci());
    }
}
