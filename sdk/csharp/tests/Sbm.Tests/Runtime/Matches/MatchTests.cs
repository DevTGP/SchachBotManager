using System.Text;
using System.Text.Json.Nodes;
using Sbm.Runtime.Referee;
using static Sbm.Tests.Runtime.Matches.ScriptedPlayer;

namespace Sbm.Tests.Runtime.Matches;

/// <summary>A whole game through the C# referee, ported from the tests of the Python SDK.</summary>
public sealed class MatchTests
{
    private static readonly object[] FoolsMateWhite = [Move("f2f3"), Move("g2g4")];
    private static readonly object[] FoolsMateBlack = [Move("e7e5"), Move("d8h4")];

    [Fact]
    public void FoolsMate()
    {
        var game = Play(
            [Ready(), .. FoolsMateWhite],
            [Ready("2.1.0-beta", "cpp"), .. FoolsMateBlack]
        );
        Assert.Equal(("0-1", "checkmate"), game.Ending);
        Assert.Equal(Color.Black, game.Outcome.Winner);
        Assert.Equal(["f2f3", "e7e5", "g2g4", "d8h4"], game.Moves);
        Assert.Equal(["init", "turn", "turn", "game_over"], game.White.SentTypes());
        Assert.Equal(["init", "turn", "turn", "game_over"], game.Black.SentTypes());
        var expected = new JsonObject
        {
            ["type"] = "game_over",
            ["result"] = "0-1",
            ["termination"] = "checkmate",
            ["last_move"] = "d8h4",
            ["fen"] = "rnb1kbnr/pppp1ppp/8/4p3/6Pq/5P2/PPPPP2P/RNBQKBNR w KQkq - 1 3",
            ["ply"] = 4,
        };
        Assert.True(JsonNode.DeepEquals(expected, game.White.Sent[^1]));
        Assert.True(JsonNode.DeepEquals(expected, game.Black.Sent[^1]));
    }

    [Fact]
    public void InitAndTurnMessages()
    {
        var settings = new MatchSettings(1000, incrementMs: 5, gameId: "g-7");
        var game = Play([Ready(), .. FoolsMateWhite], [Ready(), .. FoolsMateBlack], settings);
        var init = game.Black.Sent[0];
        var standard = Referee.Example("init.standard");
        Assert.Equal(
            standard.Select(field => field.Key).Order(StringComparer.Ordinal),
            init.Select(field => field.Key).Order(StringComparer.Ordinal)
        );
        Assert.Equal("black", Referee.Str(init, "color"));
        Assert.Equal("White Bot", Referee.Str(init, "opponent_name"));
        Assert.Equal("g-7", Referee.Str(init, "game_id"));
        Assert.Equal(5, (long)init["increment_ms"]!);
        Assert.Equal("Black Bot", Referee.Str(game.White.Sent[0], "opponent_name"));
        var first = game.White.Sent[1];
        var second = game.Black.Sent[1];
        Assert.Null(first["last_move"]);
        Assert.True(first.ContainsKey("last_move"));
        Assert.Equal(0, (int)first["ply"]!);
        Assert.Equal("f2f3", Referee.Str(second, "last_move"));
        Assert.Equal(1, (int)second["ply"]!);
        Assert.Equal(
            "rnbqkbnr/pppppppp/8/8/8/5P2/PPPPP1PP/RNBQKBNR b KQkq - 0 1",
            Referee.Str(second, "fen")
        );
        Assert.Equal("e7e5", Referee.Str(game.White.Sent[2], "last_move"));
    }

    [Fact]
    public void HookOrder()
    {
        var game = Play([Ready(), .. FoolsMateWhite], [Ready(), .. FoolsMateBlack]);
        var calls = game.White.Events.Select(item =>
            item.Kind == "send" ? Referee.Str(item.Message!, "type") : item.Kind
        );
        string[] turn = ["resume", "receive", "turn", "receive", "suspend"];
        string[] expected =
        [
            "start",
            "init",
            "receive",
            "suspend",
            .. turn,
            .. turn,
            "resume",
            "game_over",
            "close",
        ];
        Assert.Equal(expected, calls);
    }

    [Fact]
    public void BlackOpensACustomPosition()
    {
        var settings = new MatchSettings(1000, startFen: "4k3/8/8/8/8/8/8/R3K3 b - - 0 1");
        var game = Play([Ready(), Move("e1d1")], [Ready(), Move("e8d8"), Resign()], settings);
        Assert.Equal(("1-0", "resignation"), game.Ending);
        Assert.Null(game.Black.Sent[1]["last_move"]);
        Assert.Equal("e8d8", Referee.Str(game.White.Sent[1], "last_move"));
        Assert.Equal(["e8d8", "e1d1"], game.Moves);
    }

    [Fact]
    public void ClockAndIncrement()
    {
        var settings = new MatchSettings(1000, incrementMs: 100, toleranceMs: 20);
        var game = Play(
            [Ready(), new Reply(Move("f2f3"), 300), new Reply(Move("g2g4"), 815)],
            [Ready(), new Reply(Move("e7e5"), 50), Move("d8h4")],
            settings
        );
        Assert.Equal(("0-1", "checkmate"), game.Ending);
        // 1000 - 300 + 100; then 800 - 815 is within the tolerance and floors at 0.
        Assert.Equal(1000, Remaining(game.Black.Sent[1]));
        Assert.Equal(800, (long)game.Black.Sent[1]["opponent_remaining_ms"]!);
        Assert.Equal(800, Remaining(game.White.Sent[2]));
        Assert.Equal(1050, Remaining(game.Black.Sent[2]));
        Assert.Equal(100, (long)game.Black.Sent[2]["opponent_remaining_ms"]!);
    }

    [Fact]
    public void DeadlineCoversRemainingTimeAndTolerance()
    {
        var game = Play([Ready(), .. FoolsMateWhite], [Ready(), .. FoolsMateBlack]);
        // Startup, then poll and turn for each move; the fake clock stays at 0 in this game.
        var turns = game.White.Deadlines().Skip(2).Where((_, index) => index % 2 == 0);
        Assert.Equal([1020 * NsPerMs, 1020 * NsPerMs], turns);
    }

    [Fact]
    public void Timeout()
    {
        var game = Play([Ready(), new Reply(Move("e2e4"), 1021)], [Ready()]);
        Assert.Equal(("0-1", "timeout"), game.Ending);
        Assert.Equal(["init", "turn"], game.White.SentTypes());
        Assert.Equal(["init", "game_over"], game.Black.SentTypes());
        var final = game.Black.Sent[^1];
        Assert.Null(final["last_move"]);
        Assert.Equal(MatchSettings.StandardFen, Referee.Str(final, "fen"));
        Assert.Equal(0, (int)final["ply"]!);
    }

    [Fact]
    public void WaitingLineAfterTheDeadlineIsATimeout()
    {
        var game = Play([Ready(), new Reply(Move("e2e4"), 1021, Waiting: true)], [Ready()]);
        Assert.Equal(("0-1", "timeout"), game.Ending);
    }

    [Fact]
    public void ToleranceIsNotATimeout()
    {
        var game = Play([Ready(), new Reply(Move("e2e4"), 1020), Resign()], [Ready(), Resign()]);
        Assert.Equal(("1-0", "resignation"), game.Ending);
        Assert.Equal(0, (long)game.Black.Sent[1]["opponent_remaining_ms"]!);
    }

    [Fact]
    public void TimeoutAgainstABareKingIsADraw()
    {
        var settings = new MatchSettings(1000, startFen: "4k3/8/8/8/8/8/8/Q3K3 w - - 0 1");
        var game = Play([Ready(), new Reply(Move("a1a2"), 2000)], [Ready()], settings);
        Assert.Equal(("1/2-1/2", "timeout_insufficient_material"), game.Ending);
        Assert.Null(game.Outcome.Winner);
    }

    [Fact]
    public void WithoutClockNothingTimesOut()
    {
        var settings = new MatchSettings(1000, clock: false);
        var game = Play(
            [Ready(), new Reply(Move("f2f3"), 1_000_000_000), .. FoolsMateWhite[1..]],
            [new Reply(Ready(), 1_000_000_000), .. FoolsMateBlack],
            settings
        );
        Assert.Equal(("0-1", "checkmate"), game.Ending);
        var deadlines = game.White.Deadlines();
        Assert.Null(deadlines[0]);
        Assert.All(deadlines.Skip(2).Where((_, index) => index % 2 == 0), Assert.Null);
        Assert.All(
            game.White.Sent.Skip(1).SkipLast(1),
            turn => Assert.Equal(1000, Remaining(turn))
        );
    }

    [Fact]
    public void IllegalMove()
    {
        var game = Play([Ready(), Move("e2e5")], [Ready()]);
        Assert.Equal(("0-1", "illegal_move"), game.Ending);
        Assert.Contains("e2e5", game.Outcome.Detail, StringComparison.Ordinal);
        Assert.Equal(["illegal_move"], ErrorCodes(game.White));
        Assert.Equal(["init", "turn", "error", "game_over"], game.White.SentTypes());
        Assert.Equal(["init", "game_over"], game.Black.SentTypes());
    }

    [Fact]
    public void PromotionNeedsThePiece()
    {
        var settings = new MatchSettings(1000, startFen: "8/4P3/8/8/8/8/k7/4K3 w - - 0 1");
        var game = Play([Ready(), Move("e7e8")], [Ready()], settings);
        Assert.Equal(("0-1", "illegal_move"), game.Ending);
        game = Play([Ready(), Move("e7e8q"), Resign()], [Ready(), Move("a2a1")], settings);
        Assert.Equal(["e7e8q", "a2a1"], game.Moves);
    }

    public static TheoryData<string, string> TurnViolations() =>
        new()
        {
            { "{", "invalid_json" },
            { """{"type":"draw","v":1}""", "unknown_type" },
            { """{"type":"move","v":1,"move":"e2e4","extra":1}""", "schema_violation" },
            { """{"type":"move","v":1,"move":"E2E4"}""", "schema_violation" },
            { """{"type":"ready","v":1,"sdk":"1.0.0","lang":"python"}""", "unexpected_message" },
        };

    [Theory]
    [MemberData(nameof(TurnViolations))]
    public void ProtocolViolationInATurn(string line, string code)
    {
        var game = Play([Ready(), Encoding.UTF8.GetBytes(line)], [Ready()]);
        CheckViolation(game, code);
    }

    [Fact]
    public void LineTooLongInATurn()
    {
        var game = Play([Ready(), new LineTooLongException()], [Ready()]);
        CheckViolation(game, "line_too_long");
    }

    [Fact]
    public void MessageOutsideTheOwnTurn()
    {
        var game = Play([Ready(), Move("e2e4")], [Ready(), new Early(Move("e7e5"))]);
        Assert.Equal(("1-0", "protocol_violation"), game.Ending);
        Assert.Equal(["unexpected_message"], ErrorCodes(game.Black));
        Assert.Equal(["e2e4"], game.Moves);
    }

    [Theory]
    [InlineData("crash")]
    [InlineData("memory_limit")]
    public void PlayerLeavesDuringATurn(string termination)
    {
        var game = Play(
            [Ready(), new PlayerClosedException("exit code 1", termination)],
            [Ready()]
        );
        Assert.Equal(("0-1", termination), game.Ending);
        Assert.Equal(["init", "turn"], game.White.SentTypes());
        Assert.Equal(["init", "game_over"], game.Black.SentTypes());
    }

    [Fact]
    public void PlayerClosingWhileReceivingGameOverDoesNotMatter()
    {
        var time = new FakeTime();
        using var white = new Leaving("W", time, Ready(), Resign());
        using var black = new ScriptedPlayer("B", time, Ready());
        var outcome = new Match(white, black, new MatchSettings(1000), time.Now).Play();
        Assert.Equal(("0-1", "resignation"), (outcome.Result, outcome.Termination));
        Assert.Equal("game_over", black.SentTypes()[^1]);
    }

    [Fact]
    public void StartupTimeoutOfOneSide()
    {
        var game = Play([new Reply(Ready(), 10_001)], [Ready()]);
        Assert.Equal(("0-1", "startup_timeout"), game.Ending);
        Assert.Equal(["init"], game.White.SentTypes());
        Assert.Equal(["suspend", "close"], game.White.Events.TakeLast(2).Select(item => item.Kind));
        Assert.Equal(["init", "game_over"], game.Black.SentTypes());
    }

    [Fact]
    public void StartupWaitingReadyAfterTheBudgetIsATimeout()
    {
        var game = Play([Ready()], [new Reply(Ready(), 10_001, Waiting: true)]);
        Assert.Equal(("1-0", "startup_timeout"), game.Ending);
    }

    [Fact]
    public void StartupDeadline()
    {
        var settings = new MatchSettings(1000, startupMs: 500);
        var game = Play([new Reply(Ready(), 400), Resign()], [Ready()], settings);
        Assert.Equal((400 + 500) * NsPerMs, game.Black.Deadlines()[0]);
    }

    [Fact]
    public void BothFailToStart()
    {
        var game = Play(
            [new PlayerClosedException("no interpreter")],
            [new Reply(Ready(), 20_000)]
        );
        Assert.Equal(("*", "startup_timeout"), game.Ending);
        Assert.Null(game.Outcome.Winner);
        Assert.Contains("no interpreter", game.Outcome.Detail, StringComparison.Ordinal);
        Assert.Equal(["init"], game.White.SentTypes());
        Assert.Equal(["init"], game.Black.SentTypes());
    }

    public static TheoryData<string, string> StartupViolations() =>
        new()
        {
            { """{"type":"move","v":1,"move":"e2e4"}""", "unexpected_message" },
            { """{"type":"ready","v":2,"sdk":"1.0.0","lang":"python"}""", "unsupported_version" },
            { """{"type":"ready","v":1,"sdk":"1.0.0","lang":"rust"}""", "schema_violation" },
            { "ÿ", "invalid_json" },
        };

    [Theory]
    [MemberData(nameof(StartupViolations))]
    public void ProtocolViolationAtStartup(string line, string code)
    {
        var bytes = line == "ÿ" ? new byte[] { 0xff } : Encoding.UTF8.GetBytes(line);
        var game = Play([bytes], [Ready()]);
        Assert.Equal(("0-1", "protocol_violation"), game.Ending);
        Assert.Equal(["init", "error", "game_over"], game.White.SentTypes());
        Assert.Equal([code], ErrorCodes(game.White));
    }

    [Fact]
    public void StartPositionThatIsAlreadyOver()
    {
        var settings = new MatchSettings(1000, startFen: "k7/8/1Q6/8/8/8/8/7K b - - 0 1");
        var game = Play([Ready()], [Ready()], settings);
        Assert.Equal(("1/2-1/2", "stalemate"), game.Ending);
        Assert.Empty(game.Moves);
        Assert.Equal(["init", "game_over"], game.White.SentTypes());
        Assert.Equal(["init", "game_over"], game.Black.SentTypes());
    }

    [Fact]
    public void ThreefoldRepetition()
    {
        object[] white = [Move("g1f3"), Move("f3g1"), Move("g1f3"), Move("f3g1")];
        object[] black = [Move("g8f6"), Move("f6g8"), Move("g8f6"), Move("f6g8")];
        var game = Play([Ready(), .. white], [Ready(), .. black]);
        Assert.Equal(("1/2-1/2", "threefold_repetition"), game.Ending);
        Assert.Equal(8, game.Moves.Count);
    }

    [Fact]
    public void MaxMoves()
    {
        var settings = new MatchSettings(1000, maxMoves: 1);
        var game = Play([Ready(), Move("e2e4")], [Ready(), Move("e7e5")], settings);
        Assert.Equal(("1/2-1/2", "max_moves"), game.Ending);
    }

    [Fact]
    public void AMatchIsPlayedOnce()
    {
        var time = new FakeTime();
        using var white = new ScriptedPlayer("W", time, Ready(), Resign());
        using var black = new ScriptedPlayer("B", time, Ready());
        var match = new Match(white, black, new MatchSettings(1000), time.Now);
        match.Play();
        Assert.Throws<InvalidOperationException>(() => match.Play());
    }

    [Theory]
    [InlineData("")]
    [InlineData("xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx")]
    public void PlayerNamesAreChecked(string name)
    {
        var time = new FakeTime();
        using var white = new ScriptedPlayer(name, time);
        using var black = new ScriptedPlayer("B", time);
        var error = Assert.Throws<InvalidArgumentException>(() =>
            new Match(white, black, new MatchSettings(1000))
        );
        Assert.Contains("name", error.Message, StringComparison.Ordinal);
    }

    [Fact]
    public void InfrastructureErrorClosesBothPlayers()
    {
        var time = new FakeTime();
        using var white = new ScriptedPlayer("W", time, Ready(), new IOException("pipe broken"));
        using var black = new ScriptedPlayer("B", time, Ready());
        var match = new Match(white, black, new MatchSettings(1000), time.Now);
        var error = Assert.Throws<IOException>(() => match.Play());
        Assert.Equal("pipe broken", error.Message);
        Assert.Equal("close", white.Events[^1].Kind);
        Assert.Equal("close", black.Events[^1].Kind);
    }

    [Fact]
    public void PollBeforeTurnUsesTheCurrentTime()
    {
        var game = Play([new Reply(Ready(), 7), Resign()], [Ready()]);
        Assert.Equal(7 * NsPerMs, game.White.Deadlines()[1]);
    }

    private static Played Play(object[] white, object[] black, MatchSettings? settings = null)
    {
        var time = new FakeTime();
        var whitePlayer = new ScriptedPlayer("White Bot", time, white);
        var blackPlayer = new ScriptedPlayer("Black Bot", time, black);
        var match = new Match(
            whitePlayer,
            blackPlayer,
            settings ?? new MatchSettings(1000),
            time.Now
        );
        var outcome = match.Play();
        Assert.Equal("close", whitePlayer.Events[^1].Kind);
        Assert.Equal("close", blackPlayer.Events[^1].Kind);
        return new Played(outcome, [.. match.Moves], whitePlayer, blackPlayer);
    }

    private static void CheckViolation(Played game, string code)
    {
        Assert.Equal(("0-1", "protocol_violation"), game.Ending);
        Assert.Equal([code], ErrorCodes(game.White));
        Assert.Equal("game_over", game.White.SentTypes()[^1]);
    }

    private static string[] ErrorCodes(ScriptedPlayer player) =>
        [
            .. player
                .Sent.Where(message => Referee.Str(message, "type") == "error")
                .Select(message => Referee.Str(message, "code")),
        ];

    private static long Remaining(JsonObject turn) => (long)turn["remaining_ms"]!;

    private sealed record Played(
        Outcome Outcome,
        List<string> Moves,
        ScriptedPlayer White,
        ScriptedPlayer Black
    )
    {
        public (string, string) Ending => (Outcome.Result, Outcome.Termination);
    }

    private sealed class Leaving(string name, FakeTime time, params object[] script)
        : ScriptedPlayer(name, time, script)
    {
        internal override void Send(Action<System.Text.Json.Utf8JsonWriter> message)
        {
            base.Send(message);
            if (Referee.Str(Sent[^1], "type") == "game_over")
            {
                throw new PlayerClosedException("gone");
            }
        }
    }
}
