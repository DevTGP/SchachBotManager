using System.Net;
using System.Net.Sockets;
using System.Text;
using System.Text.Json.Nodes;
using Sbm.Runtime;
using Sbm.Runtime.Viewer;
using Sbm.Tests.Runtime.Viewer;

namespace Sbm.Tests.Runtime;

/// <summary>Sdk.Run without the process: exit code, options, log file, viewer and transports.</summary>
[Collection(SharedLog.Name)]
public sealed class RunnerTests : IDisposable
{
    private static readonly JsonObject[] OneGame =
    [
        Referee.Example("init.standard"),
        Referee.Example("turn.first_move"),
        Referee.Example("game_over.checkmate"),
    ];

    private readonly LogCapture _log = new();
    private MemoryStream _output = new();
    private readonly StringWriter _stderr = new();
    private readonly TextWriter _consoleError = Console.Error;
    private readonly string _dir = Directory.CreateTempSubdirectory("sbm-runner-").FullName;

    public RunnerTests()
    {
        Console.SetError(_stderr);
        ViewerWindow.Reset();
    }

    public void Dispose()
    {
        ViewerWindow.Reset();
        ViewerWindow.FindProgram = ViewerProgram.Path;
        ViewerWindow.StartProgram = ViewerProgram.Start;
        Console.SetError(_consoleError);
        _log.Dispose();
        _output.Dispose();
        _stderr.Dispose();
        Directory.Delete(_dir, recursive: true);
    }

    [Fact]
    public void GameEndsWithZero()
    {
        Assert.Equal(0, Run(() => new FirstMoveBot()));
        Assert.Equal(["ready", "move"], Types());
        Assert.Equal("", _log.Text);
        Assert.Equal("", _stderr.ToString());
    }

    [Fact]
    public void ConstructorExceptionEndsWithOne()
    {
        Assert.Equal(1, Run(() => throw new InvalidOperationException("boom")));
        Assert.Empty(Types());
        Assert.Contains("ERROR MyBot() raised InvalidOperationException: boom\n", _log.Text);
    }

    [Fact]
    public void CallbackExceptionEndsWithOne()
    {
        Assert.Equal(1, Run(() => new ThrowingBot()));
        Assert.Equal(["ready"], Types());
        Assert.Contains("ERROR ChooseMove raised InvalidOperationException: boom\n", _log.Text);
        Assert.Contains(nameof(ThrowingBot.ChooseMove), _log.Text);
    }

    [Fact]
    public void ProtocolErrorEndsWithOne()
    {
        var turn = Referee.Turn(Referee.StartFen, 0);
        Assert.Equal(1, Run(() => new FirstMoveBot(), messages: [turn]));
        Assert.Contains("ERROR protocol error: ", _log.Text);
    }

    [Fact]
    public void InvalidOptionsEndWithOne()
    {
        var opened = false;
        var code = Runner.Run(
            () => new FirstMoveBot(),
            "MyBot",
            false,
            ["--tcp", "0"],
            _ => null,
            _ =>
            {
                opened = true;
                return Referee.Channel(OneGame, _output);
            }
        );
        Assert.Equal(1, code);
        Assert.False(opened);
        Assert.StartsWith("sbm: invalid port '0'", _stderr.ToString(), StringComparison.Ordinal);
    }

    [Fact]
    public void LogLevelAndFileFromTheOptions()
    {
        var path = Path.Combine(_dir, "bot.log");
        string[] args = ["--log-level", "debug", "--log-file", path];
        Assert.Equal(0, Run(() => new LoggingBot(), args));
        Assert.Equal(0, Run(() => new LoggingBot(), args, new() { ["SBM_LOG_LEVEL"] = "error" }));
        Log.Info("after the game");
        var lines = File.ReadAllLines(path, Encoding.UTF8);
        Assert.Equal(2, lines.Length);
        Assert.All(
            lines,
            line => Assert.EndsWith(" [ply 0] DEBUG thinking", line, StringComparison.Ordinal)
        );
        Assert.Contains("after the game", _log.Text);
    }

    [Fact]
    public void LogLevelFromTheEnvironment()
    {
        Assert.Equal(0, Run(() => new LoggingBot(), env: new() { ["SBM_LOG_LEVEL"] = "off" }));
        Assert.Equal("", _log.Text);
        Assert.Equal(LogLevel.Off, Log.Level());
    }

    [Fact]
    public void UnopenableLogFile()
    {
        var path = Path.Combine(_dir, "missing", "bot.log");
        Assert.Equal(1, Run(() => new FirstMoveBot(), ["--log-file", path]));
        Assert.StartsWith(
            "sbm: cannot open the log file: ",
            _stderr.ToString(),
            StringComparison.Ordinal
        );
        Assert.Empty(Types());
    }

    [Fact]
    public void ViewerShowsTheGameAndHoldsTheProgram()
    {
        var process = FakeViewer();
        Assert.Equal(0, Run(() => new FirstMoveBot(), viewer: true));
        Assert.Equal(["start", "move", "game_over"], process.Types().Where(type => type != "log"));
        Assert.True(process.Waited);
        Assert.True(process.InputClosed);
        Assert.Contains("viewer: the program ends when the viewer window is closed", _log.Text);
    }

    [Fact]
    public void ViewerWaitsAfterAnError()
    {
        var process = FakeViewer();
        Assert.Equal(1, Run(() => new ThrowingBot(), viewer: true));
        Assert.True(process.Waited);
        Assert.Contains(
            process.Messages(),
            message =>
                Referee.Str(message, "type") == "log"
                && Referee.Str(message, "level") == "error"
                && Referee.Str(message, "text").StartsWith("ChooseMove raised", StringComparison.Ordinal)
        );
    }

    [Fact]
    public void ViewerMissingInThisInstallation()
    {
        ViewerWindow.FindProgram = () => Path.Combine(_dir, "sbm-viewer");
        Assert.Equal(0, Run(() => new FirstMoveBot(), viewer: true));
        Assert.Contains("WARN  viewer: sbm-viewer is not part of this installation", _log.Text);
    }

    [Fact]
    public void NoViewerWithoutTheArgument()
    {
        var process = FakeViewer();
        Assert.Equal(0, Run(() => new FirstMoveBot()));
        Assert.Empty(process.Messages());
        Assert.False(process.Waited);
    }

    [Fact]
    public void NoViewerOnTheServer()
    {
        var process = FakeViewer();
        var env = new Dictionary<string, string> { ["SBM_NO_VIEWER"] = "1" };
        Assert.Equal(0, Run(() => new FirstMoveBot(), env: env, viewer: true));
        Assert.Equal("", _log.Text);
        Assert.Empty(process.Messages());
    }

    [Fact]
    public void RemoteIsNotAvailableYet()
    {
        Assert.Equal(1, Run(() => new FirstMoveBot(), ["--remote", "https://example.org"]));
        Assert.Contains("ERROR the transport remote is not available in this SDK yet", _log.Text);
        Assert.Empty(Types());
    }

    [Fact]
    public void UnreachableArena()
    {
        var code = Runner.Run(
            () => new FirstMoveBot(),
            "MyBot",
            false,
            ["--tcp", "7471"],
            _ => null,
            _ => throw new SocketException((int)SocketError.ConnectionRefused)
        );
        Assert.Equal(1, code);
        Assert.Contains("ERROR cannot connect to the arena on 127.0.0.1:7471: ", _log.Text);
    }

    [Fact]
    public async Task TcpTransport()
    {
        using var listener = new TcpListener(IPAddress.Loopback, 0);
        listener.Start();
        var port = ((IPEndPoint)listener.LocalEndpoint).Port;
        var cancel = TestContext.Current.CancellationToken;
        var bot = Task.Run(
            () =>
                Runner.Run(
                    () => new FirstMoveBot(),
                    "MyBot",
                    false,
                    ["--tcp", port.ToString(System.Globalization.CultureInfo.InvariantCulture)],
                    _ => null
                ),
            cancel
        );
        using (var arena = await listener.AcceptTcpClientAsync(cancel))
        {
            var stream = arena.GetStream();
            using var reader = new StreamReader(stream, Encoding.UTF8);
            var data = string.Concat(OneGame.Select(message => message.ToJsonString() + "\n"));
            await stream.WriteAsync(Encoding.UTF8.GetBytes(data), cancel);
            Assert.Equal("ready", Referee.Str(Parse(await reader.ReadLineAsync(cancel)), "type"));
            Assert.Equal("move", Referee.Str(Parse(await reader.ReadLineAsync(cancel)), "type"));
            Assert.Null(await reader.ReadLineAsync(cancel));
        }
        Assert.Equal(0, await bot);
    }

    private int Run(
        Func<Bot> create,
        string[]? args = null,
        Dictionary<string, string>? env = null,
        JsonObject[]? messages = null,
        bool viewer = false
    )
    {
        _output = new MemoryStream();
        return Runner.Run(
            create,
            "MyBot",
            viewer,
            args ?? [],
            name => env?.GetValueOrDefault(name),
            _ => Referee.Channel(messages ?? OneGame, _output)
        );
    }

    private FakeViewerProcess FakeViewer()
    {
        var program = Path.Combine(_dir, "sbm-viewer");
        File.WriteAllBytes(program, []);
        var process = new FakeViewerProcess();
        ViewerWindow.FindProgram = () => program;
        ViewerWindow.StartProgram = _ => process;
        return process;
    }

    private IEnumerable<string> Types() =>
        Referee.Answers(_output).Select(answer => Referee.Str(answer, "type"));

    private static JsonObject Parse(string? line) => JsonNode.Parse(line!)!.AsObject();

    private sealed class ThrowingBot : Bot
    {
        public override Move ChooseMove(Board board, Clock clock) =>
            throw new InvalidOperationException("boom");
    }

    private sealed class LoggingBot : FirstMoveBot
    {
        public override Move ChooseMove(Board board, Clock clock)
        {
            Log.Debug("thinking");
            return base.ChooseMove(board, clock);
        }
    }
}
