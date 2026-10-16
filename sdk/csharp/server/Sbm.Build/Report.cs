using System.Text.Json;

namespace Sbm.Build;

/// <summary>
/// The JSON the runner reads (verifikation.md): {"ruleset", "analysis", "build", "program"};
/// a section is {"ok", "truncated", "findings"} as in the Python analyzer, build is null after a
/// failed analysis, program the compiled bot in Base64 or null.
/// </summary>
internal static class Report
{
    public static void Write(Stream output, BuildResult result)
    {
        using var json = new Utf8JsonWriter(output);
        json.WriteStartObject();
        json.WriteString("ruleset", result.Ruleset);
        json.WritePropertyName("analysis");
        WriteSection(json, result.Analysis);
        json.WritePropertyName("build");
        if (result.Build is null)
        {
            json.WriteNullValue();
        }
        else
        {
            WriteSection(json, result.Build);
        }
        if (result.Program is null)
        {
            json.WriteNull("program");
        }
        else
        {
            json.WriteBase64String("program", result.Program);
        }
        json.WriteEndObject();
    }

    private static void WriteSection(Utf8JsonWriter json, Section section)
    {
        json.WriteStartObject();
        json.WriteBoolean("ok", section.Ok);
        json.WriteBoolean("truncated", section.Truncated);
        json.WriteStartArray("findings");
        foreach (var finding in section.Findings)
        {
            json.WriteStartObject();
            json.WriteString("rule", finding.Rule);
            json.WriteString("file", finding.File);
            if (finding.Line is { } line)
            {
                json.WriteNumber("line", line);
            }
            else
            {
                json.WriteNull("line");
            }
            json.WriteString("message", finding.Message);
            json.WriteEndObject();
        }
        json.WriteEndArray();
        json.WriteEndObject();
    }
}
