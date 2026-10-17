using Sbm.Runtime;
using Sbm.Runtime.Play;
using Sbm.Runtime.Remote;
using Sbm.Tests.Runtime.Remote;

namespace Sbm.Tests.Runtime.Play;

/// <summary>Sdk.Play (E120): local games on the C# referee and games on the server.</summary>
[Collection(SharedLog.Name)]
public sealed class StarterTests : IDisposable
{
    private static readonly string[] Results = ["1-0", "0-1", "1/2-1/2"];

    // Answers init and resigns at its first turn, without the SDK.
    private const string Resigner = """
        import json, sys

        for line in sys.stdin:
            kind = json.loads(line)["type"]
            if kind == "init":
                answer = {"type": "ready", "v": 1, "sdk": "1.0.0", "lang": "python"}
            elif kind == "turn":
                answer = {"type": "resign", "v": 1}
            else:
                break
            print(json.dumps(answer), flush=True)
        """;

    private readonly LogCapture _log = new();
    private readonly DirectoryInfo _folder = Directory.CreateTempSubdirectory("sbm-play-");

    public void Dispose()
    {
        _folder.Delete(recursive: true);
        _log.Dispose();
    }

    [Fact]
    public void LocalGamesAlternateColors()
    {
        var (played, code) = Play(
            new("random")
            {
                Color = "white",
                Time = "5+0",
                Games = 2,
            }
        );
        Assert.Equal(0, code);
        Assert.Equal([Color.White, Color.Black], played.Select(game => game.Color));
        Assert.Equal(["local-1", "local-2"], played.Select(game => game.GameId));
        Assert.All(played, game => Assert.Equal("random", game.OpponentName));
        Assert.All(played, game => Assert.Contains(game.Result, Results));
        Assert.Contains("INFO  game 1/2 (local-1) as white against random: ", _log.Text);
        Assert.Contains("INFO  game 2/2 (local-2) as black against random: ", _log.Text);
        Assert.Matches(
            @"INFO  score [0-9.]+/2: \d won, \d drawn, \d lost, 0 without result",
            _log.Text
        );
    }

    [Fact]
    public void ABotAgainstItselfGetsNumberedNames()
    {
        var (played, _) = Play(new("material") { Color = "black", Time = "5+0" }, "material");
        Assert.Equal("material-2", Assert.Single(played).OpponentName);
    }

    [Fact]
    public void AnOpponentThatCannotStartLoses()
    {
        var (played, code) = Play(new("sbm-no-such-program --x") { Color = "white" });
        Assert.Equal(0, code);
        var game = Assert.Single(played);
        Assert.Equal(
            ("sbm-no-such-program", "1-0", "crash"),
            (game.OpponentName, game.Result, game.Termination)
        );
        Assert.Contains("score 1/1: 1 won, 0 drawn, 0 lost, 0 without result", _log.Text);
    }

    [Fact]
    public void APythonFileIsAProcess()
    {
        var program = OperatingSystem.IsWindows() ? "python" : "python3";
        Assert.SkipWhen(!OnPath(program), $"{program} is not installed");
        var path = Path.Combine(_folder.FullName, "resigner.py");
        File.WriteAllText(path, Resigner);
        foreach (var color in new[] { "white", "black" })
        {
            var (played, code) = Play(new(path) { Color = color, Time = "10+0" });
            Assert.Equal(0, code);
            var game = Assert.Single(played);
            Assert.Equal("resigner", game.OpponentName);
            Assert.Equal("resignation", game.Termination);
            Assert.Equal(color == "white" ? "1-0" : "0-1", game.Result);
        }
    }

    [Fact]
    public void AnExceptionOfTheBotEndsTheSeries()
    {
        var (played, code) = Starter.Play(
            () => new Broken(),
            "Broken",
            new("random")
            {
                Color = "white",
                Time = "5+0",
                Games = 3,
            },
            _ => null
        );
        Assert.Equal(1, code);
        Assert.Empty(played);
        Assert.Contains("no idea", _log.Text);
        Assert.DoesNotContain("score ", _log.Text);
    }

    private static readonly PlayRequest[] InvalidRequests =
    [
        new(""),
        new("random") { Color = "red" },
        new("random") { Games = 0 },
        new("random") { Time = "fast" },
        new("random") { Discipline = "Blitz" },
        new("tcp"),
        new("tcp:7470"),
        new("no/such/bot.py"),
        new("\"open"),
        new("Material") { Server = "ftp://example.org", Token = FakeServer.Token },
        new("Material") { Server = "example.org", Token = FakeServer.Token },
        new("Material") { Server = "https://example.org" },
        new("Material")
        {
            Server = "https://example.org",
            Token = FakeServer.Token,
            Time = "60+1",
            Discipline = "Blitz",
        },
        new("Material")
        {
            Server = "https://example.org",
            Token = FakeServer.Token,
            Time = "soon",
        },
    ];

    public static TheoryData<int> InvalidRequestIndexes() =>
        [.. Enumerable.Range(0, InvalidRequests.Length)];

    [Theory]
    [MemberData(nameof(InvalidRequestIndexes))]
    public void InvalidArguments(int index)
    {
        var error = Assert.Throws<InvalidArgumentException>(() => Play(InvalidRequests[index]));
        Assert.StartsWith("play: ", error.Message, StringComparison.Ordinal);
    }

    [Fact]
    public void RemoteGamesAlternateColors()
    {
        using var server = new FakeServer();
        var request = new PlayRequest("Material")
        {
            Server = server.Url,
            Token = FakeServer.Token,
            Color = "black",
            Games = 2,
        };
        var (played, code) = Play(request);
        Assert.Equal(0, code);
        Assert.Equal(
            ["black", "white"],
            server.Requests.Select(seen => Referee.Str(seen.Body, "color"))
        );
        var first = server.Requests.First().Body;
        Assert.Equal(60_000, (long)first["initial_time_ms"]!);
        Assert.Equal(1000, (long)first["increment_ms"]!);
        // The fake server always sends the same init and game_over.
        var game = new PlayedGame(
            FakeServer.MatchId,
            Color.White,
            "Stockfisch Junior",
            "0-1",
            "checkmate"
        );
        Assert.Equal([game, game], played);
        Assert.Contains("score 0/2: 0 won, 0 drawn, 2 lost, 0 without result", _log.Text);
    }

    [Fact]
    public void TheTokenCanComeFromTheEnvironment()
    {
        using var server = new FakeServer();
        var request = new PlayRequest("Material") { Server = server.Url, Discipline = "Blitz" };
        var (_, code) = Starter.Play(
            () => new FirstMoveBot(),
            "MyBot",
            request,
            name => name == Starter.TokenVariable ? FakeServer.Token : null
        );
        Assert.Equal(0, code);
        var (_, headers, body) = Assert.Single(server.Requests);
        Assert.Equal($"Bearer {FakeServer.Token}", headers["authorization"]);
        Assert.Equal("Blitz", Referee.Str(body, "discipline"));
        Assert.False(body.ContainsKey("initial_time_ms"));
    }

    [Fact]
    public void PlayWaitsWhileThePreviousGameEnds()
    {
        using var server = new FakeServer();
        var request = new PlayRequest("Material") { Server = server.Url, Token = FakeServer.Token };
        var attempts = 0;
        var waits = new List<TimeSpan>();
        var (played, code) = Starter.Play(
            () => new FirstMoveBot(),
            "MyBot",
            request,
            _ => null,
            remote =>
            {
                if (++attempts < 3)
                {
                    throw new RemoteException("finish your running game", RemoteGame.BusyCode);
                }
                return RemoteOpening.Open(remote);
            },
            waits.Add
        );
        Assert.Equal(0, code);
        Assert.Equal("checkmate", Assert.Single(played).Termination);
        Assert.Equal([RemoteGame.BusyWait, RemoteGame.BusyWait], waits);
    }

    [Fact]
    public void ABusyServerGivesUpAfterHalfAMinute()
    {
        var request = new PlayRequest("Material")
        {
            Server = "https://example.org",
            Token = FakeServer.Token,
        };
        var waits = 0;
        var (played, code) = Starter.Play(
            () => new FirstMoveBot(),
            "MyBot",
            request,
            _ => null,
            _ => throw new RemoteException("finish your running game", RemoteGame.BusyCode),
            _ => waits++
        );
        Assert.Equal((1, 0), (code, played.Count));
        Assert.Equal(RemoteGame.BusyAttempts - 1, waits);
        Assert.Contains("ERROR play stopped: finish your running game", _log.Text);
    }

    [Fact]
    public void ARefusedGameEndsTheSeries()
    {
        using var server = new FakeServer
        {
            Answer = (404, """{"code":"no_opponent","message":"no bot named Nobody"}"""),
        };
        var request = new PlayRequest("Nobody")
        {
            Server = server.Url,
            Token = FakeServer.Token,
            Games = 2,
        };
        var (played, code) = Play(request);
        Assert.Equal((1, 0), (code, played.Count));
        Assert.Single(server.Requests);
        Assert.Contains(
            "ERROR play stopped: the server refused the game (no_opponent): no bot named Nobody",
            _log.Text
        );
    }

    private static (IReadOnlyList<PlayedGame> Games, int Code) Play(
        PlayRequest request,
        string botName = "MyBot"
    ) => Starter.Play(() => new FirstMoveBot(), botName, request, _ => null);

    private static bool OnPath(string program) =>
        (Environment.GetEnvironmentVariable("PATH") ?? "")
            .Split(Path.PathSeparator, StringSplitOptions.RemoveEmptyEntries)
            .Any(folder =>
                File.Exists(Path.Combine(folder, program))
                || File.Exists(Path.Combine(folder, program + ".exe"))
            );

    private sealed class Broken : Bot
    {
        public override Move ChooseMove(Board board, Clock clock) =>
            throw new InvalidOperationException("no idea");
    }
}
