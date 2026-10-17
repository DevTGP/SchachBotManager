using System.Text.Json.Nodes;
using Sbm.Runtime;
using Sbm.Runtime.Remote;

namespace Sbm.Tests.Runtime.Remote;

/// <summary>Transport remote (E116): the request for a game, the seat and a whole game.</summary>
[Collection(SharedLog.Name)]
public sealed class RemoteTests : IDisposable
{
    private readonly LogCapture _log = new();
    private readonly FakeServer _server = new();

    public void Dispose()
    {
        _server.Dispose();
        _log.Dispose();
    }

    [Fact]
    public void RequestSendsTheTokenAndNamesTheSocket()
    {
        var body = new JsonObject { ["opponent"] = "Material", ["color"] = "white" };
        var seat = GameRequest.Request(_server.Url + "/", FakeServer.Token, body);
        Assert.Equal(
            new Seat(FakeServer.MatchId, FakeServer.Seat, "white", _server.SocketUrl),
            seat
        );
        var (path, headers, sent) = Assert.Single(_server.Requests);
        Assert.Equal(GameRequest.ApiPath, path);
        Assert.Equal($"Bearer {FakeServer.Token}", headers["authorization"]);
        Assert.Equal("1", headers["x-sbm-csrf"]);
        Assert.Equal(GameRequest.UserAgent, headers["user-agent"]);
        Assert.StartsWith("application/json", headers["content-type"], StringComparison.Ordinal);
        Assert.True(JsonNode.DeepEquals(body, sent));
    }

    [Fact]
    public void RequestKeepsThePathOfTheSite()
    {
        var seat = GameRequest.Request(_server.Url + "/chess/", FakeServer.Token, []);
        Assert.Equal("/chess" + GameRequest.ApiPath, Assert.Single(_server.Requests).Path);
        Assert.Equal($"ws://127.0.0.1:{_server.Port}/chess{FakeServer.SocketPath}", seat.SocketUrl);
    }

    [Fact]
    public void RequestReportsTheErrorOfTheApi()
    {
        _server.Answer = (
            429,
            """{"code":"too_many_games","message":"finish your running game","field":"x"}"""
        );
        var error = Assert.Throws<RemoteException>(() => Request());
        Assert.Equal("too_many_games", error.Code);
        Assert.Equal(
            "the server refused the game (too_many_games): x: finish your running game",
            error.Message
        );
    }

    [Fact]
    public void RequestWithoutAnErrorBody()
    {
        _server.Answer = (502, "<html>bad gateway</html>");
        var error = Assert.Throws<RemoteException>(() => Request());
        Assert.Equal(RemoteException.Network, error.Code);
        Assert.Equal("the server refused the game (network): HTTP 502", error.Message);
    }

    [Fact]
    public void RequestWithAnIncompleteAnswer()
    {
        _server.Answer = (201, """{"match_id":"m"}""");
        var error = Assert.Throws<RemoteException>(() => Request());
        Assert.StartsWith($"cannot reach {_server.Url}: ", error.Message, StringComparison.Ordinal);
    }

    [Theory]
    [InlineData("ftp://example.org")]
    [InlineData("example.org")]
    [InlineData("")]
    public void RequestNeedsHttp(string url)
    {
        var error = Assert.Throws<RemoteException>(() =>
            GameRequest.Request(url, FakeServer.Token, [])
        );
        Assert.Equal("usage", error.Code);
        Assert.Equal($"--remote needs an http or https address, not '{url}'", error.Message);
    }

    [Fact]
    public void UnreachableServer()
    {
        var url = _server.Url;
        _server.Dispose();
        var error = Assert.Throws<RemoteException>(() =>
            GameRequest.Request(url, FakeServer.Token, [])
        );
        Assert.Equal(RemoteException.Network, error.Code);
        Assert.StartsWith($"cannot reach {url}: ", error.Message, StringComparison.Ordinal);
    }

    [Fact]
    public void BodyWithTheTime()
    {
        var remote = new RemoteOptions("https://example.org", FakeServer.Token, "Material")
        {
            Time = "30+0.5",
        };
        var expected = new JsonObject
        {
            ["opponent"] = "Material",
            ["color"] = "random",
            ["initial_time_ms"] = 30_000,
            ["increment_ms"] = 500,
        };
        Assert.True(JsonNode.DeepEquals(expected, RemoteOpening.RequestBody(remote)));
    }

    [Fact]
    public void DisciplineWinsOverTheTime()
    {
        var remote = new RemoteOptions("https://example.org", FakeServer.Token, "Material")
        {
            Color = "black",
            Discipline = "Blitz",
            Time = "nonsense",
        };
        var expected = new JsonObject
        {
            ["opponent"] = "Material",
            ["color"] = "black",
            ["discipline"] = "Blitz",
        };
        Assert.True(JsonNode.DeepEquals(expected, RemoteOpening.RequestBody(remote)));
    }

    [Fact]
    public void InvalidTimeIsAUsageError()
    {
        var remote = new RemoteOptions("https://example.org", FakeServer.Token, "M") { Time = "x" };
        var error = Assert.Throws<RemoteException>(() => RemoteOpening.RequestBody(remote));
        Assert.Equal("usage", error.Code);
        Assert.StartsWith("invalid time control 'x'", error.Message, StringComparison.Ordinal);
    }

    [Fact]
    public void JoinReceivesTheGame()
    {
        using var channel = RemoteChannel.Join(
            new Seat(FakeServer.MatchId, FakeServer.Seat, "white", _server.SocketUrl)
        );
        var init = channel.Receive();
        Assert.Equal("init", init?.GetProperty("type").GetString());
        Assert.Equal(["join"], _server.ReceivedTypes());
        var join = Assert.Single(_server.Received);
        Assert.Equal(FakeServer.MatchId, Referee.Str(join, "match_id"));
        Assert.Equal(1, join["v"]!.GetValue<int>());
    }

    [Fact]
    public void RefusedSeat()
    {
        var error = Assert.Throws<RemoteException>(() =>
            RemoteChannel.Join(new Seat(FakeServer.MatchId, "B", "white", _server.SocketUrl))
        );
        Assert.Equal("no_game", error.Code);
        Assert.Equal("the server refused the seat (no_game)", error.Message);
    }

    [Fact]
    public void RunPlaysARemoteGameAndAnswersPings()
    {
        using var server = new FakeServer(ping: TimeSpan.FromMilliseconds(300));
        var env = new Dictionary<string, string> { ["SBM_TOKEN"] = FakeServer.Token };
        string[] args = ["--remote", server.Url, "--opponent", "Material", "--time", "60+1"];
        Assert.Equal(0, Run(() => new SlowBot(), args, env));
        var expected = new JsonObject
        {
            ["opponent"] = "Material",
            ["color"] = "random",
            ["initial_time_ms"] = 60_000,
            ["increment_ms"] = 1000,
        };
        Assert.True(JsonNode.DeepEquals(expected, Assert.Single(server.Requests).Body));
        Assert.Equal(["join", "ready", "move"], server.ReceivedTypes());
        Assert.Contains(
            $"INFO  remote game {FakeServer.MatchId} against Material, playing white",
            _log.Text
        );
    }

    [Fact]
    public void RunReportsARefusedGame()
    {
        _server.Answer = (404, """{"code":"no_opponent","message":"no bot named Nobody"}""");
        string[] args = ["--remote", _server.Url, "--token", FakeServer.Token, "--opponent", "N"];
        Assert.Equal(1, Run(() => new FirstMoveBot(), args));
        Assert.Contains(
            "ERROR the server refused the game (no_opponent): no bot named Nobody",
            _log.Text
        );
    }

    [Fact]
    public void RunReportsAGatewayThatDoesNotSwitch()
    {
        _server.Answer = (
            201,
            new JsonObject
            {
                ["match_id"] = FakeServer.MatchId,
                ["seat"] = FakeServer.Seat,
                ["color"] = "white",
                ["socket_path"] = "/missing",
            }.ToJsonString()
        );
        string[] args = ["--remote", _server.Url, "--token", FakeServer.Token, "--opponent", "N"];
        Assert.Equal(1, Run(() => new FirstMoveBot(), args));
        Assert.Contains($"ERROR cannot connect to {_server.Url}: ", _log.Text);
    }

    private Seat Request() => GameRequest.Request(_server.Url, FakeServer.Token, []);

    private static int Run(
        Func<Bot> create,
        string[] args,
        Dictionary<string, string>? env = null
    ) => Runner.Run(create, "MyBot", false, args, name => env?.GetValueOrDefault(name));

    /// <summary>Thinks longer than the gateway waits for a pong, so the SDK must answer pings.</summary>
    private sealed class SlowBot : Bot
    {
        public override Move ChooseMove(Board board, Clock clock)
        {
            Thread.Sleep(1500);
            return board.LegalMoves()[0];
        }
    }
}
