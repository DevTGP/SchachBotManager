using System.Text.Json.Nodes;
using Sbm.Runtime;

namespace Sbm.Tests.Runtime;

/// <summary>One game against a scripted referee: init, turns, game_over and the bot's answers.</summary>
[Collection(SharedLog.Name)]
public sealed class GameTests : IDisposable
{
    private static readonly string Start = Referee.StartFen;
    private static readonly JsonObject Init = Referee.Example("init.standard");
    private static readonly JsonObject GameOver = Referee.Example("game_over.checkmate");
    private static readonly JsonObject BlackInit = Referee.With(Init, "color", "black");

    private readonly LogCapture _log = new();

    public void Dispose() => _log.Dispose();

    [Fact]
    public void WhiteGame()
    {
        var bot = new FirstMoveBot();
        var answers = Referee.Play(bot, Init, Referee.Example("turn.first_move"), GameOver);
        Assert.Equal(
            $$"""{"type":"ready","v":1,"sdk":"{{Sdk.Version}}","lang":"csharp"}""",
            answers[0].ToJsonString()
        );
        var first = new Board().LegalMoves()[0].Uci();
        Assert.Equal($$"""{"type":"move","v":1,"move":"{{first}}"}""", answers[1].ToJsonString());
        Assert.Equal(2, answers.Count);
        Assert.Equal(
            new GameInfo(
                "66f1c2a9e4b0a1b2c3d4e5f6",
                Color.White,
                "Stockfisch Junior",
                Start,
                300000,
                2000,
                10000,
                1024,
                "Blitz 5+2"
            ),
            Assert.Single(bot.Starts)
        );
        var (fen, clock) = Assert.Single(bot.Turns);
        Assert.Equal(Start, fen);
        Assert.Equal(300000, clock.RemainingMs());
        Assert.Equal(300000, clock.OpponentRemainingMs());
        Assert.Equal(2000, clock.IncrementMs());
        Assert.Equal(new GameResult("0-1", "checkmate"), Assert.Single(bot.Ends));
        Assert.Equal("", _log.Text);
    }

    [Fact]
    public void BlackFollowsTheOpponentMoves()
    {
        var bot = new FirstMoveBot();
        var promotion = Referee.Example("turn.after_promotion");
        var king = Board.FromFen(Referee.Str(promotion, "fen"));
        king.MakeMove(king.LegalMoves()[0]);
        var after = king.Copy();
        var reply = after.LegalMoves()[^1];
        after.MakeMove(reply);
        var later = Referee.Turn(after.Fen(), 121, reply.Uci());
        var answers = Referee.Play(
            bot,
            Referee.Example("init.black_custom_position"),
            promotion,
            later,
            GameOver
        );
        Assert.Equal(["ready", "move", "move"], answers.Select(a => Referee.Str(a, "type")));
        Assert.Equal(Referee.Str(promotion, "fen"), bot.Turns[0].Fen);
        Assert.Equal(after.Fen(), bot.Turns[1].Fen);
        Assert.Equal("", _log.Text);
    }

    [Fact]
    public void EnPassantSquareWithoutCaptureIsNoMismatch()
    {
        Referee.Play(
            new FirstMoveBot(),
            BlackInit,
            Referee.Example("turn.after_opponent_move"),
            GameOver
        );
        Assert.Equal("", _log.Text);
    }

    [Fact]
    public void MismatchAdoptsTheRefereePosition()
    {
        var bot = new FirstMoveBot();
        const string other = "rnbqkbnr/pppppppp/8/8/3P4/8/PPP1PPPP/RNBQKBNR b KQkq - 0 1";
        Referee.Play(bot, BlackInit, Referee.Turn(other, 1, "e2e4"), GameOver);
        Assert.Equal(other, Assert.Single(bot.Turns).Fen);
        Assert.Contains("WARN  own position differs", _log.Text, StringComparison.Ordinal);
    }

    [Fact]
    public void UnparsableLastMoveIsRepairedByTheFen()
    {
        var bot = new FirstMoveBot();
        var fen = Referee.Str(Referee.Example("turn.after_opponent_move"), "fen");
        Referee.Play(bot, BlackInit, Referee.Turn(fen, 1, "e2e5"), GameOver);
        Assert.Equal(Board.FromFen(fen).Fen(), Assert.Single(bot.Turns).Fen);
        Assert.Contains("WARN  own position differs", _log.Text, StringComparison.Ordinal);
    }

    [Fact]
    public void BotChangesToItsBoardStayLocal()
    {
        var bot = new MutatingBot();
        var first = new Board();
        first.MakeMove(first.LegalMoves()[0]);
        var reply = first.LegalMoves()[0];
        first.MakeMove(reply);
        Referee.Play(
            bot,
            Init,
            Referee.Turn(Start, 0),
            Referee.Turn(first.Fen(), 2, reply.Uci()),
            GameOver
        );
        Assert.Equal(first.Fen(), bot.Turns[1].Fen);
        Assert.Equal("", _log.Text);
    }

    [Fact]
    public void Resign()
    {
        var answers = Referee.Play(new AnswerBot(Move.Resign), Init, Referee.Turn(Start, 0));
        Assert.Equal("""{"type":"resign","v":1}""", answers[1].ToJsonString());
    }

    [Fact]
    public void ReportBelongsToOneTurn()
    {
        var second = Board.FromFen("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 2");
        var answers = Referee.Play(
            new ReportingBot(),
            Init,
            Referee.Turn(Start, 0),
            Referee.Turn(second.Fen(), 2),
            GameOver
        );
        Assert.Equal("""{"depth":3,"text":"first"}""", answers[1]["info"]!.ToJsonString());
        Assert.False(answers[2].ContainsKey("info"));
    }

    [Fact]
    public void ReportBeforeTheTurnIsDropped()
    {
        var answers = Referee.Play(new EarlyBot(), Init, Referee.Turn(Start, 0), GameOver);
        Assert.False(answers[1].ContainsKey("info"));
    }

    [Fact]
    public void ReportNeedsAnInfo() =>
        Assert.Throws<ArgumentNullException>(() => new FirstMoveBot().Report(null!));

    [Fact]
    public void NullMoveIsNoAnswer()
    {
        var error = Assert.Throws<BotFailureException>(() =>
            Referee.Play(new AnswerBot(Move.NullMove), Init, Referee.Turn(Start, 0), GameOver)
        );
        Assert.Contains("no UCI form", error.Message, StringComparison.Ordinal);
    }

    [Theory]
    [InlineData("OnGameStart")]
    [InlineData("ChooseMove")]
    [InlineData("OnGameEnd")]
    public void ExceptionsInCallbacks(string callback)
    {
        var error = Assert.Throws<BotFailureException>(() =>
            Referee.Play(new FailingBot(callback), Init, Referee.Turn(Start, 0), GameOver)
        );
        Assert.Equal($"{callback} raised InvalidOperationException: boom", error.Message);
        Assert.IsType<InvalidOperationException>(error.InnerException);
        Assert.StartsWith(
            $"{error.Message}\nSystem.InvalidOperationException: boom",
            Guard.Describe(error),
            StringComparison.Ordinal
        );
    }

    [Fact]
    public void IllegalOwnMoveIsLeftToTheReferee()
    {
        var answers = Referee.Play(
            new AnswerBot(Move.Parse("e2e5")),
            Init,
            Referee.Turn(Start, 0),
            GameOver
        );
        Assert.Equal("e2e5", Referee.Str(answers[1], "move"));
        Assert.Contains("WARN  own move e2e5 is not legal", _log.Text, StringComparison.Ordinal);
    }

    [Fact]
    public void UnknownTypesAndFieldsAreIgnored()
    {
        var init = Referee.With(Init, "future_field", new JsonObject { ["x"] = 1 });
        var answers = Referee.Play(
            new FirstMoveBot(),
            init,
            new JsonObject { ["type"] = "ping" },
            Referee.With(Referee.Turn(Start, 0), "hint", "e2e4"),
            GameOver
        );
        Assert.Equal(["ready", "move"], answers.Select(a => Referee.Str(a, "type")));
        Assert.Contains(
            "WARN  ignoring a message of unknown type \"ping\"",
            _log.Text,
            StringComparison.Ordinal
        );
    }

    [Fact]
    public void RefereeErrorsAreLogged()
    {
        Referee.Play(new FirstMoveBot(), Init, Referee.Example("error.illegal_move"), GameOver);
        Assert.Contains(
            "ERROR referee reports illegal_move: e1g1: castling through check",
            _log.Text,
            StringComparison.Ordinal
        );
    }

    [Fact]
    public void UnsupportedVersionStillAnswersReady()
    {
        var init = Referee.With(Init, "supported", new JsonArray(2));
        var answers = Referee.Play(new FirstMoveBot(), init, GameOver);
        Assert.Equal("ready", Referee.Str(answers[0], "type"));
        Assert.Contains(
            "ERROR the referee supports protocol versions [2]",
            _log.Text,
            StringComparison.Ordinal
        );
    }

    [Fact]
    public void EndOfInputBeforeGameOver()
    {
        Referee.Play(new FirstMoveBot(), Init, Referee.Turn(Start, 0));
        Assert.Contains("WARN  input ended before game_over", _log.Text, StringComparison.Ordinal);
    }

    [Fact]
    public void PlyAppearsInLogLines()
    {
        Referee.Play(new LoggingBot(), Init, Referee.Turn(Start, 0), GameOver);
        Assert.Contains("[ply 0] INFO  thinking", _log.Text, StringComparison.Ordinal);
    }

    public static TheoryData<string> ProtocolErrorCases() => [.. ProtocolErrors.Keys];

    [Theory]
    [MemberData(nameof(ProtocolErrorCases))]
    public void ProtocolErrorsEndTheGame(string name) =>
        Assert.Throws<ProtocolException>(() =>
            Referee.Play(new FirstMoveBot(), [.. ProtocolErrors[name]()])
        );

    public static TheoryData<string> InitExamples() => [.. Referee.ExampleNames("init")];

    [Theory]
    [MemberData(nameof(InitExamples))]
    public void AllInitExamples(string name)
    {
        var init = Referee.Example(name);
        using var document = System.Text.Json.JsonDocument.Parse(init.ToJsonString());
        var info = Protocol.GameInfo(document.RootElement);
        Assert.Equal(Referee.Str(init, "start_fen"), info.StartFen);
        Assert.Contains(Protocol.Supported(document.RootElement), Protocol.IsThisVersion);
    }

    public static TheoryData<string> GameOverExamples() => [.. Referee.ExampleNames("game_over")];

    [Theory]
    [MemberData(nameof(GameOverExamples))]
    public void AllGameOverExamples(string name)
    {
        var gameOver = Referee.Example(name);
        using var document = System.Text.Json.JsonDocument.Parse(gameOver.ToJsonString());
        Assert.Equal(
            new GameResult(Referee.Str(gameOver, "result"), Referee.Str(gameOver, "termination")),
            Protocol.GameResult(document.RootElement)
        );
    }

    private static readonly Dictionary<string, Func<JsonObject[]>> ProtocolErrors = new()
    {
        ["turn before init"] = () => [Referee.Turn(Start, 0)],
        ["second init"] = () => [Init, Init],
        ["unknown color"] = () => [Referee.With(Init, "color", "red")],
        ["invalid start fen"] = () => [Referee.With(Init, "start_fen", "no fen")],
        ["boolean increment"] = () => [Referee.With(Init, "increment_ms", true)],
        ["missing discipline"] = () => [Referee.Without(Init, "discipline")],
        ["invalid turn fen"] = () =>
            [Init, Referee.With(Referee.Turn(Start, 0), "fen", "8/8/8/8/8/8/8/8 w - - 0 1")],
        ["string time"] = () =>
            [Init, Referee.With(Referee.Turn(Start, 0), "remaining_ms", "1000")],
        ["fractional ply"] = () => [Init, Referee.With(Referee.Turn(Start, 0), "ply", 1.5)],
        ["game_over without termination"] = () =>
            [Init, new JsonObject { ["type"] = "game_over", ["result"] = "1-0" }],
    };

    private sealed class MutatingBot : FirstMoveBot
    {
        public override Move ChooseMove(Board board, Clock clock)
        {
            var move = base.ChooseMove(board, clock);
            board.MakeMove(board.LegalMoves()[0]);
            board.MakeMove(board.LegalMoves()[0]);
            return move;
        }
    }

    private sealed class AnswerBot(Move answer) : FirstMoveBot
    {
        public override Move ChooseMove(Board board, Clock clock) => answer;
    }

    private sealed class ReportingBot : FirstMoveBot
    {
        public override Move ChooseMove(Board board, Clock clock)
        {
            if (board.FullmoveNumber() == 1)
            {
                Report(new Info { Depth = 3, Text = "first" });
            }
            return base.ChooseMove(board, clock);
        }
    }

    private sealed class EarlyBot : FirstMoveBot
    {
        public override void OnGameStart(GameInfo info) => Report(new Info { Depth = 1 });
    }

    private sealed class LoggingBot : FirstMoveBot
    {
        public override Move ChooseMove(Board board, Clock clock)
        {
            Log.Info("thinking");
            return base.ChooseMove(board, clock);
        }
    }

    private sealed class FailingBot(string callback) : FirstMoveBot
    {
        public override void OnGameStart(GameInfo info) => Fail("OnGameStart");

        public override Move ChooseMove(Board board, Clock clock)
        {
            Fail("ChooseMove");
            return base.ChooseMove(board, clock);
        }

        public override void OnGameEnd(GameResult result) => Fail("OnGameEnd");

        private void Fail(string name)
        {
            if (name == callback)
            {
                throw new InvalidOperationException("boom");
            }
        }
    }
}
