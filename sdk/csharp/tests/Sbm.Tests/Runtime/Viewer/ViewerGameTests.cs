using Sbm.Runtime.Viewer;

namespace Sbm.Tests.Runtime.Viewer;

/// <summary>A game reports its moves to an open viewer window (E106).</summary>
[Collection(SharedLog.Name)]
public sealed class ViewerGameTests : IDisposable
{
    private static readonly string Start = Referee.StartFen;

    private readonly LogCapture _log = new(LogLevel.Off);
    private readonly string _dir = Directory.CreateTempSubdirectory("sbm-viewer-").FullName;
    private readonly FakeViewerProcess _process = new();

    public ViewerGameTests()
    {
        ViewerWindow.Reset();
        var program = Path.Combine(_dir, "sbm-viewer");
        File.WriteAllBytes(program, []);
        ViewerWindow.FindProgram = () => program;
        ViewerWindow.StartProgram = _ => _process;
    }

    public void Dispose()
    {
        ViewerWindow.Reset();
        ViewerWindow.FindProgram = ViewerProgram.Path;
        ViewerWindow.StartProgram = ViewerProgram.Start;
        _log.Dispose();
        Directory.Delete(_dir, recursive: true);
    }

    [Fact]
    public void GameAsWhite()
    {
        Assert.NotNull(ViewerWindow.Open(_ => null));
        var first = new Board().LegalMoves()[0].Uci();
        var reply = Board.FromFen(After(Start, first)).LegalMoves()[0].Uci();
        var secondTurn = Referee.Turn(After(Start, first, reply), 2, reply, remainingMs: 800);
        var gameOver = Referee.Example("game_over.checkmate");
        Referee.Play(
            new FirstMoveBot(),
            Referee.Example("init.standard"),
            Referee.Example("turn.first_move"),
            secondTurn,
            gameOver
        );
        Assert.Equal(["start", "move", "move", "move", "game_over"], _process.Types());
        var messages = _process.Messages();
        var (start, own, opponent, ownAgain, end) = (
            messages[0],
            messages[1],
            messages[2],
            messages[3],
            messages[4]
        );
        Assert.Equal("FirstMoveBot", Referee.Str(start, "bot"));
        Assert.Equal("white", Referee.Str(start, "color"));
        Assert.Equal("Stockfisch Junior", Referee.Str(start, "opponent"));
        Assert.Equal(1, own["ply"]!.GetValue<int>());
        Assert.Equal(first, Referee.Str(own, "move"));
        Assert.Equal("bot", Referee.Str(own, "by"));
        Assert.Equal(After(Start, first), Referee.Str(own, "fen"));
        Assert.Equal(300000, own["black_ms"]!.GetValue<long>());
        Assert.InRange(own["white_ms"]!.GetValue<long>(), 0, 300000 + 2000);
        Assert.True(own["elapsed_ms"]!.GetValue<long>() >= 0);
        Assert.Equal(2, opponent["ply"]!.GetValue<int>());
        Assert.Equal(reply, Referee.Str(opponent, "move"));
        Assert.Equal("opponent", Referee.Str(opponent, "by"));
        Assert.Equal(800, opponent["white_ms"]!.GetValue<long>());
        Assert.Equal(2000, opponent["black_ms"]!.GetValue<long>());
        Assert.Equal(3, ownAgain["ply"]!.GetValue<int>());
        Assert.Equal("bot", Referee.Str(ownAgain, "by"));
        Assert.True(System.Text.Json.Nodes.JsonNode.DeepEquals(gameOver, end));
    }

    [Fact]
    public void InfoGoesWithTheMove()
    {
        Assert.NotNull(ViewerWindow.Open(_ => null));
        Referee.Play(
            new ReportingBot(),
            Referee.Example("init.standard"),
            Referee.Example("turn.first_move"),
            Referee.Example("game_over.checkmate")
        );
        var move = _process.Messages()[1];
        Assert.Equal("""{"depth":2,"text":"thinking"}""", move["info"]!.ToJsonString());
    }

    [Fact]
    public void NoWindowNoMessages()
    {
        Referee.Play(
            new FirstMoveBot(),
            Referee.Example("init.standard"),
            Referee.Example("turn.first_move"),
            Referee.Example("game_over.checkmate")
        );
        Assert.Empty(_process.Messages());
    }

    [Fact]
    public void ResignationIsNotAMove()
    {
        Assert.NotNull(ViewerWindow.Open(_ => null));
        Referee.Play(
            new ResigningBot(),
            Referee.Example("init.standard"),
            Referee.Example("turn.first_move"),
            Referee.Example("game_over.checkmate")
        );
        Assert.Equal(["start", "game_over"], _process.Types());
    }

    private static string After(string fen, params string[] moves)
    {
        var board = Board.FromFen(fen);
        foreach (var uci in moves)
        {
            board.MakeMove(board.ParseMove(uci));
        }
        return board.Fen();
    }

    private sealed class ResigningBot : Bot
    {
        public override Move ChooseMove(Board board, Clock clock) => Move.Resign;
    }

    private sealed class ReportingBot : FirstMoveBot
    {
        public override Move ChooseMove(Board board, Clock clock)
        {
            Report(new Info { Depth = 2, Text = "thinking" });
            return base.ChooseMove(board, clock);
        }
    }
}
