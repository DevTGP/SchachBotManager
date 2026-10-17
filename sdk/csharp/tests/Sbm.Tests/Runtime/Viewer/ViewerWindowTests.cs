using System.Text.Json;
using Sbm.Runtime.Viewer;

namespace Sbm.Tests.Runtime.Viewer;

/// <summary>The viewer window of a bot program, with a fake process instead of the viewer (E106).</summary>
[Collection(SharedLog.Name)]
public sealed class ViewerWindowTests : IDisposable
{
    private readonly LogCapture _log = new();
    private readonly string _dir = Directory.CreateTempSubdirectory("sbm-viewer-").FullName;

    public ViewerWindowTests() => ViewerWindow.Reset();

    public void Dispose()
    {
        ViewerWindow.Reset();
        ViewerWindow.FindProgram = ViewerProgram.Path;
        ViewerWindow.StartProgram = ViewerProgram.Start;
        _log.Dispose();
        Directory.Delete(_dir, recursive: true);
    }

    [Fact]
    public void ClocksFollowTheColorOfTheBot()
    {
        var process = new FakeViewerProcess();
        var window = new ViewerWindow(process);
        window.GameStarted("Material", ViewerFiles.BlackInfo);
        window.MovePlayed(1, "e2e4", ViewerFiles.AfterE4, false, (300000, 299000));
        var messages = process.Messages();
        Assert.Equal("black", Referee.Str(messages[0], "color"));
        Assert.Equal(299000, messages[1]["white_ms"]!.GetValue<long>());
        Assert.Equal(300000, messages[1]["black_ms"]!.GetValue<long>());
    }

    [Fact]
    public void GameOverSendsTheFinalMoveFirst()
    {
        var process = new FakeViewerProcess();
        var gameOver = Referee.Example("game_over.with_final_position");
        new ViewerWindow(process).GameOver(Element(gameOver));
        var messages = process.Messages();
        Assert.Equal(2, messages.Count);
        Assert.Equal(
            $$"""{"type":"move","ply":7,"move":"h5f7","fen":"{{Referee.Str(gameOver, "fen")}}","by":"opponent"}""",
            messages[0].ToJsonString()
        );
        Assert.True(System.Text.Json.Nodes.JsonNode.DeepEquals(gameOver, messages[1]));
    }

    [Fact]
    public void GameOverWithoutAFinalMove()
    {
        var process = new FakeViewerProcess();
        var gameOver = Referee.Example("game_over.aborted_before_first_move");
        new ViewerWindow(process).GameOver(Element(gameOver));
        Assert.Equal(["game_over"], process.Types());
    }

    [Fact]
    public void ClosedWindowStaysSilent()
    {
        var process = new FakeViewerProcess { Broken = true };
        var window = new ViewerWindow(process);
        window.GameStarted("Material", ViewerFiles.BlackInfo);
        Assert.False(window.IsOpen);
        process.Broken = false;
        window.LogLine(LogLevel.Info, "12:00:00.000", "lost");
        Assert.Empty(process.Messages());
    }

    [Fact]
    public void EndedProcessIsNotOpen()
    {
        var process = new FakeViewerProcess();
        var window = new ViewerWindow(process);
        Assert.True(window.IsOpen);
        process.HasExited = true;
        Assert.False(window.IsOpen);
    }

    [Fact]
    public void WaitUntilClosedHoldsTheProgram()
    {
        var process = new FakeViewerProcess();
        new ViewerWindow(process).WaitUntilClosed();
        Assert.True(process.Waited);
        Assert.True(process.InputClosed);
        Assert.Contains(
            "INFO  viewer: the program ends when the viewer window is closed",
            _log.Text
        );
    }

    [Fact]
    public void MissingProgramIsReportedOnce()
    {
        ViewerWindow.FindProgram = () => Path.Combine(_dir, "sbm-viewer");
        Assert.Null(ViewerWindow.Open(_ => null));
        Assert.Null(ViewerWindow.Open(_ => null));
        Assert.Single(
            _log.Text.Split('\n'),
            line => line.Contains("WARN  viewer: sbm-viewer is not part of this installation")
        );
        Assert.Null(ViewerWindow.Active);
    }

    [Fact]
    public void OpenWindowFeedsTheLog()
    {
        var process = StartFake();
        var window = ViewerWindow.Open(_ => null);
        Assert.NotNull(window);
        Assert.Same(window, ViewerWindow.Open(_ => null));
        Assert.Same(window, ViewerWindow.Active);
        Log.Warn("careful");
        Log.Debug("not written at level INFO");
        var line = Assert.Single(process.Messages());
        Assert.Equal("log", Referee.Str(line, "type"));
        Assert.Equal("warn", Referee.Str(line, "level"));
        Assert.Equal("careful", Referee.Str(line, "text"));
    }

    [Fact]
    public void NoViewerKeepsTheWindowShut()
    {
        var process = StartFake();
        Assert.Null(ViewerWindow.Open(name => name == "SBM_NO_VIEWER" ? "1" : null));
        Assert.Empty(process.Messages());
        Assert.Equal("", _log.Text);
    }

    [Fact]
    public void UnstartableProgramIsReported()
    {
        StartFake();
        ViewerWindow.StartProgram = _ => throw new IOException("not executable");
        Assert.Null(ViewerWindow.Open(_ => null));
        Assert.Contains("WARN  viewer: cannot start sbm-viewer: not executable", _log.Text);
    }

    [Fact]
    public void AWarningWhileSendingDoesNotRecurse()
    {
        var process = StartFake();
        var window = ViewerWindow.Open(_ => null)!;
        window.Send(json =>
        {
            Log.Warn("written while sending");
            ViewerMessages.Log(json, LogLevel.Info, "12:00:00.000", "first");
        });
        var line = Assert.Single(process.Messages());
        Assert.Equal("first", Referee.Str(line, "text"));
        Assert.Contains("written while sending", _log.Text);
    }

    private FakeViewerProcess StartFake()
    {
        var program = Path.Combine(_dir, "sbm-viewer");
        File.WriteAllBytes(program, []);
        var process = new FakeViewerProcess();
        ViewerWindow.FindProgram = () => program;
        ViewerWindow.StartProgram = _ => process;
        return process;
    }

    private static JsonElement Element(System.Text.Json.Nodes.JsonObject message) =>
        JsonDocument.Parse(message.ToJsonString()).RootElement;
}
