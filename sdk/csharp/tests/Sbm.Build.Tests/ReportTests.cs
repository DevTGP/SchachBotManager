using System.Text.Json;

namespace Sbm.Build.Tests;

public class ReportTests
{
    [Fact]
    public void A_built_bot_has_its_program()
    {
        using var bot = new Workspace().Add("Bot.cs", Text.Bot());
        var result = bot.Build();

        using var json = Write(result);

        var root = json.RootElement;
        Assert.Equal("csharp-1", root.GetProperty("ruleset").GetString());
        Assert.True(root.GetProperty("analysis").GetProperty("ok").GetBoolean());
        Assert.True(root.GetProperty("build").GetProperty("ok").GetBoolean());
        Assert.Equal(result.Program, root.GetProperty("program").GetBytesFromBase64());
    }

    [Fact]
    public void A_refused_bot_has_findings_and_no_build()
    {
        using var bot = new Workspace().Add("Bot.cs", Text.Bot("void M() => Console.Beep();"));

        using var json = Write(bot.Build());

        var root = json.RootElement;
        var analysis = root.GetProperty("analysis");
        Assert.False(analysis.GetProperty("ok").GetBoolean());
        Assert.False(analysis.GetProperty("truncated").GetBoolean());
        var finding = analysis.GetProperty("findings")[0];
        Assert.Equal(
            ["rule", "file", "line", "message"],
            finding.EnumerateObject().Select(property => property.Name)
        );
        Assert.Equal("Bot.cs", finding.GetProperty("file").GetString());
        Assert.Equal(JsonValueKind.Null, root.GetProperty("build").ValueKind);
        Assert.Equal(JsonValueKind.Null, root.GetProperty("program").ValueKind);
    }

    [Fact]
    public void A_finding_without_a_place_has_a_null_line()
    {
        var result = new BuildResult(
            "csharp-1",
            new Section([]),
            new Section([new Finding("SBM2004", "", null, "native")]),
            null
        );

        using var json = Write(result);

        var finding = json.RootElement.GetProperty("build").GetProperty("findings")[0];
        Assert.Equal(JsonValueKind.Null, finding.GetProperty("line").ValueKind);
    }

    private static JsonDocument Write(BuildResult result)
    {
        using var stream = new MemoryStream();
        Report.Write(stream, result);
        return JsonDocument.Parse(stream.ToArray());
    }
}
