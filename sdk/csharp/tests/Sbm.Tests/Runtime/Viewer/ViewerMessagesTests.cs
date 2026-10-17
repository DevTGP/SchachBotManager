using System.Text.Json;
using System.Text.Json.Nodes;
using Sbm.Runtime;
using Sbm.Runtime.Viewer;

namespace Sbm.Tests.Runtime.Viewer;

/// <summary>The messages to the viewer, compared with spec/protocol/viewer-v1/ (E106).</summary>
public sealed class ViewerMessagesTests
{
    private static readonly string AfterE4 = ViewerFiles.AfterE4;

    [Fact]
    public void Start()
    {
        var message = Encode(json => ViewerMessages.Start(json, "Material", ViewerFiles.BlackInfo));
        Assert.Equal(
            $$"""{"type":"start","v":1,"bot":"Material","color":"black","opponent":"Random","start_fen":"{{new Board().Fen()}}","initial_time_ms":300000,"increment_ms":2000,"discipline":"Blitz"}""",
            message.ToJsonString()
        );
    }

    [Fact]
    public void StartWithoutDisciplineAndWithALongName()
    {
        var info = ViewerFiles.BlackInfo with { Discipline = "", Color = Color.White };
        var message = Encode(json => ViewerMessages.Start(json, new string('B', 100), info));
        Assert.False(message.ContainsKey("discipline"));
        Assert.Equal(new string('B', ViewerMessages.MaxNameLength), Referee.Str(message, "bot"));
        Assert.Equal("white", Referee.Str(message, "color"));
        Assert.Equal(
            ViewerFiles.Example("start.without_discipline").Select(pair => pair.Key).Order(),
            message.Select(pair => pair.Key).Order()
        );
    }

    [Fact]
    public void MoveWithClocksAndInfo()
    {
        var info = InfoFields.Json(
            new Info
            {
                Depth = 3,
                ScoreCp = 25,
                Pv = [Move.Parse("e2e4"), Move.Parse("e7e5")],
            }
        );
        var message = Encode(json =>
            ViewerMessages.Move(json, 1, "e2e4", AfterE4, true, (299500, 300000), 500, info)
        );
        Assert.True(JsonNode.DeepEquals(ViewerFiles.Example("move.own"), message));
    }

    [Fact]
    public void MoveWithoutClocksAndNegativeTimes()
    {
        var message = Encode(json => ViewerMessages.Move(json, 1, "e2e4", AfterE4, false, null));
        Assert.Equal(
            $$"""{"type":"move","ply":1,"move":"e2e4","fen":"{{AfterE4}}","by":"opponent"}""",
            message.ToJsonString()
        );
        var clamped = Encode(json =>
            ViewerMessages.Move(json, 1, "e2e4", AfterE4, true, (-5, 10), -1, "{}")
        );
        Assert.Equal(0, clamped["white_ms"]!.GetValue<long>());
        Assert.Equal(10, clamped["black_ms"]!.GetValue<long>());
        Assert.Equal(0, clamped["elapsed_ms"]!.GetValue<long>());
        Assert.False(clamped.ContainsKey("info"));
    }

    [Theory]
    [InlineData(LogLevel.Trace, "debug")]
    [InlineData(LogLevel.Debug, "debug")]
    [InlineData(LogLevel.Info, "info")]
    [InlineData(LogLevel.Warn, "warn")]
    [InlineData(LogLevel.Error, "error")]
    public void LogLevels(byte level, string name)
    {
        var message = Encode(json => ViewerMessages.Log(json, level, "12:00:00.250", "text"));
        Assert.Equal(name, Referee.Str(message, "level"));
    }

    [Fact]
    public void LogLine()
    {
        var message = Encode(json =>
            ViewerMessages.Log(json, LogLevel.Info, "14:03:07.125", "searching depth 3")
        );
        Assert.True(JsonNode.DeepEquals(ViewerFiles.Example("log.info"), message));
        var longText = Encode(json =>
            ViewerMessages.Log(json, LogLevel.Info, "14:03:07.125", new string('x', 5000))
        );
        Assert.Equal(ViewerMessages.MaxLogLength, Referee.Str(longText, "text").Length);
    }

    internal static JsonObject Encode(Action<Utf8JsonWriter> write) =>
        JsonNode.Parse(JsonLines.Text(write))!.AsObject();
}
