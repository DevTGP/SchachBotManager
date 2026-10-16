using System.Buffers;
using System.Text;
using System.Text.Json;
using Sbm.Runtime;

namespace Sbm.Tests.Runtime;

/// <summary>Info in the move message: limits of the protocol, truncation and dropped fields (E43, E63).</summary>
[Collection(SharedLog.Name)]
public sealed class InfoFieldsTests : IDisposable
{
    private readonly LogCapture _log = new(LogLevel.Debug);

    public void Dispose() => _log.Dispose();

    private static string Encode(Info info)
    {
        var buffer = new ArrayBufferWriter<byte>();
        using (var json = new Utf8JsonWriter(buffer))
        {
            InfoFields.Write(json, info);
        }
        return Encoding.UTF8.GetString(buffer.WrittenSpan);
    }

    private static JsonElement Parse(Info info) => JsonDocument.Parse(Encode(info)).RootElement;

    [Fact]
    public void FullInfo()
    {
        var board = new Board();
        var info = new Info
        {
            Depth = 12,
            Seldepth = 18,
            ScoreCp = -35,
            Nodes = 1_534_211,
            Pv = [board.ParseMove("e2e4"), Move.Parse("e7e5")],
            Text = "book",
        };
        Assert.Equal(
            """{"depth":12,"seldepth":18,"score_cp":-35,"nodes":1534211,"pv":["e2e4","e7e5"],"text":"book"}""",
            Encode(info)
        );
        Assert.Equal("", _log.Text);
    }

    [Fact]
    public void EmptyInfo() => Assert.Equal("{}", Encode(new Info()));

    [Fact]
    public void LimitsAreInclusive()
    {
        Assert.Equal(
            """{"depth":0,"seldepth":1024,"score_cp":-100000,"nodes":0}""",
            Encode(
                new Info
                {
                    Depth = 0,
                    Seldepth = 1024,
                    ScoreCp = -100_000,
                    Nodes = 0,
                }
            )
        );
        Assert.Equal(
            """{"depth":1024,"seldepth":0,"score_cp":100000,"nodes":9007199254740991}""",
            Encode(
                new Info
                {
                    Depth = 1024,
                    Seldepth = 0,
                    ScoreCp = 100_000,
                    Nodes = InfoFields.MaxNodes,
                }
            )
        );
        Assert.Equal("""{"score_mate":-1024}""", Encode(new Info { ScoreMate = -1024 }));
        Assert.Equal("""{"score_mate":1024}""", Encode(new Info { ScoreMate = 1024 }));
        Assert.Equal("", _log.Text);
    }

    public static TheoryData<string, long> InvalidIntegers() =>
        new()
        {
            { "depth", -1 },
            { "depth", 1025 },
            { "seldepth", -1 },
            { "seldepth", 1025 },
            { "score_cp", -100_001 },
            { "score_cp", 100_001 },
            { "score_mate", 0 },
            { "score_mate", -1025 },
            { "score_mate", 1025 },
            { "nodes", -1 },
            { "nodes", InfoFields.MaxNodes + 1 },
        };

    [Theory]
    [MemberData(nameof(InvalidIntegers))]
    public void InvalidIntegersAreLeftOut(string name, long value)
    {
        var info = name switch
        {
            "depth" => new Info { Depth = (int)value },
            "seldepth" => new Info { Seldepth = (int)value },
            "score_cp" => new Info { ScoreCp = (int)value },
            "score_mate" => new Info { ScoreMate = (int)value },
            _ => new Info { Nodes = value },
        };
        Assert.Equal("{}", Encode(info));
        Assert.Contains(
            $"WARN  report: {name}={value} is outside the protocol limits",
            _log.Text,
            StringComparison.Ordinal
        );
    }

    [Fact]
    public void BothScoresKeepMate()
    {
        Assert.Equal("""{"score_mate":3}""", Encode(new Info { ScoreCp = 50, ScoreMate = 3 }));
        Assert.Contains(
            "score_cp and score_mate are both set",
            _log.Text,
            StringComparison.Ordinal
        );
    }

    [Fact]
    public void PvIsTruncated()
    {
        var move = Move.Parse("g1f3");
        var pv = Parse(new Info { Pv = [.. Enumerable.Repeat(move, 40)] }).GetProperty("pv");
        Assert.Equal(InfoFields.MaxPvMoves, pv.GetArrayLength());
        Assert.Contains(
            "DEBUG report: pv truncated to 32 moves",
            _log.Text,
            StringComparison.Ordinal
        );
    }

    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public void PvEndsBeforeAMoveWithoutUci(bool resign)
    {
        var bad = resign ? Move.Resign : Move.NullMove;
        var info = new Info { Pv = [Move.Parse("e2e4"), bad, Move.Parse("e7e5")] };
        Assert.Equal("""{"pv":["e2e4"]}""", Encode(info));
        Assert.Contains("WARN  report: pv ends before", _log.Text, StringComparison.Ordinal);
    }

    [Fact]
    public void TextIsTruncatedByCodePoints()
    {
        var text = Parse(new Info { Text = string.Concat(Enumerable.Repeat("♗😀", 200)) })
            .GetProperty("text")
            .GetString()!;
        Assert.Equal(InfoFields.MaxTextLength, text.EnumerateRunes().Count());
        Assert.StartsWith("♗😀♗", text, StringComparison.Ordinal);
    }

    [Fact]
    public void TextWithoutUtf8Form() =>
        Assert.Equal("a�b", Parse(new Info { Text = "a\uD800b" }).GetProperty("text").GetString());
}
