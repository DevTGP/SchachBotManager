namespace Sbm.Tests;

/// <summary>Errors as C# exceptions and arguments that the vectors do not cover (E49).</summary>
public class ErrorTests
{
    private const string Start = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1";

    [Theory]
    [InlineData(typeof(InvalidArgumentException))]
    [InlineData(typeof(InvalidFenException))]
    [InlineData(typeof(InvalidUciException))]
    [InlineData(typeof(IllegalMoveException))]
    [InlineData(typeof(InvalidStateException))]
    [InlineData(typeof(DataNotFoundException))]
    public void Hierarchy(Type error)
    {
        Assert.Equal(typeof(ChessException), error.BaseType);
        Assert.True(error.IsSealed);
        Assert.True(typeof(Exception).IsAssignableFrom(typeof(ChessException)));
    }

    [Fact]
    public void EmbeddedNul()
    {
        Assert.Throws<InvalidFenException>(() => Board.FromFen(Start + "\0x"));
        Assert.Throws<InvalidUciException>(() => Move.Parse("e2e4\0"));
        Assert.Throws<InvalidUciException>(() => new Board().ParseMove("e2e4\0"));
    }

    [Fact]
    public void NullText()
    {
        Assert.Throws<ArgumentNullException>(() => Board.FromFen(null!));
        Assert.Throws<ArgumentNullException>(() => Move.Parse(null!));
        Assert.Throws<ArgumentNullException>(() => new Board().ParseMove(null!));
    }

    [Fact]
    public void MessageNamesTheCallAndMove()
    {
        var board = new Board();
        var error = Assert.Throws<IllegalMoveException>(() => board.MakeMove(Move.Parse("e2e5")));
        Assert.Contains(
            "Board.MakeMove(<Move e2e5 flags=0>)",
            error.Message,
            StringComparison.Ordinal
        );
        Assert.Equal(Start, board.Fen());
    }

    [Fact]
    public void UndoWithoutMove()
    {
        var error = Assert.Throws<InvalidStateException>(() => new Board().UndoMove());
        Assert.Contains("Board.UndoMove", error.Message, StringComparison.Ordinal);
    }

    [Theory]
    [InlineData(64, Square.E4, MoveFlags.Quiet)]
    [InlineData(Square.E2, 255, MoveFlags.Quiet)]
    [InlineData(Square.E2, Square.E4, 6)]
    [InlineData(Square.E2, Square.E4, 7)]
    [InlineData(Square.E2, Square.E4, 16)]
    public void MoveOutOfRange(byte from, byte to, byte flags) =>
        Assert.Throws<InvalidArgumentException>(() => new Move(from, to, flags));

    [Fact]
    public void ValuesOutOfRange()
    {
        var board = new Board();
        Assert.Throws<InvalidArgumentException>(() => board.PieceAt(64));
        Assert.Throws<InvalidArgumentException>(() => board.AttackersOf(Square.E4, 3));
        Assert.Throws<InvalidArgumentException>(() => Move.FromValue(0x6000));
    }
}
