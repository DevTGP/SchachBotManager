using System.Text;
using Sbm.Runtime.Referee;

namespace Sbm.Tests.Runtime.Matches;

/// <summary>
/// Strict reading of bot lines (E66): the examples of spec/protocol/v1 and the edge cases of
/// the Python SDK, whose verdicts the schemas decide there.
/// </summary>
public sealed class BotMessagesTests
{
    private static readonly string[] Prefixes = ["bot_message.", "ready.", "move.", "resign."];

    private const string Move = "{\"type\":\"move\",\"v\":1,\"move\":\"e2e4\"";

    public static TheoryData<string> Valid() => Examples("valid");

    public static TheoryData<string> Invalid() => Examples("invalid");

    [Theory]
    [MemberData(nameof(Valid))]
    public void ValidExamplesAreAccepted(string path) =>
        Assert.True(Accepts(File.ReadAllText(path)), path);

    [Theory]
    [MemberData(nameof(Invalid))]
    public void InvalidExamplesAreRejected(string path) =>
        Assert.False(Accepts(File.ReadAllText(path)), path);

    public static TheoryData<string, bool> EdgeCases() =>
        new()
        {
            // Integers as JSON Schema sees them
            { """{"type":"move","v":1.0,"move":"e2e4"}""", true },
            { """{"type":"move","v":true,"move":"e2e4"}""", false },
            { """{"type":"move","v":"1","move":"e2e4"}""", false },
            { """{"type":"move","v":2,"move":"e2e4"}""", false },
            { """{"type":"ready","v":1.0,"sdk":"1.0.0","lang":"python"}""", true },
            { """{"type":"ready","v":2,"sdk":"1.0.0","lang":"python"}""", false },
            { """{"type":"ready","v":false,"sdk":"1.0.0","lang":"python"}""", false },
            { Info("""{"depth":3.0}"""), true },
            { Info("""{"depth":3.5}"""), false },
            { Info("""{"depth":true}"""), false },
            { Info("""{"depth":-1}"""), false },
            { Info("""{"depth":1024}"""), true },
            { Info("""{"depth":1025}"""), false },
            { Info("""{"seldepth":0}"""), true },
            { Info("""{"nodes":9007199254740991}"""), true },
            { Info("""{"nodes":9007199254740992}"""), false },
            { Info("""{"score_cp":-100000}"""), true },
            { Info("""{"score_cp":100001}"""), false },
            { Info("""{"score_mate":0}"""), false },
            { Info("""{"score_mate":-1}"""), true },
            { Info("""{"score_mate":1025}"""), false },
            { Info("""{"score_cp":1,"score_mate":1}"""), false },
            // Strings and patterns
            { """{"type":"move","v":1,"move":"e7e8q"}""", true },
            { """{"type":"move","v":1,"move":"e7e8k"}""", false },
            { """{"type":"move","v":1,"move":"e2e4 "}""", false },
            { """{"type":"move","v":1,"move":"e2e4\n"}""", false },
            { """{"type":"move","v":1,"move":"0000"}""", false },
            { """{"type":"move","v":1,"move":null}""", false },
            { Ready("1.2.3-rc.1+build.5"), true },
            { Ready("01.2.3"), false },
            { Ready("1.2"), false },
            { Ready("1.2.3\\n"), false },
            { Ready("1." + new string('1', 62)), false },
            { Ready("1.0." + new string('1', 61)), false },
            { """{"type":"ready","v":1,"sdk":"1.0.0","lang":"Python"}""", false },
            { """{"type":"ready","v":1,"sdk":"1.0.0","lang":["python"]}""", false },
            { Info("""{"text":""}"""), true },
            { Info($$"""{"text":"{{Repeat("ä", 256)}}"}"""), true },
            { Info($$"""{"text":"{{Repeat("😀", 256)}}"}"""), true },
            { Info($$"""{"text":"{{Repeat("x", 257)}}"}"""), false },
            { Info("""{"text":null}"""), false },
            { Info("""{"pv":[]}"""), true },
            { Info($$"""{"pv":[{{Pv(32)}}]}"""), true },
            { Info($$"""{"pv":[{{Pv(33)}}]}"""), false },
            { Info("""{"pv":"e2e4"}"""), false },
            { Info("""{"pv":["e2e4",5]}"""), false },
            // Structure
            { "{}", false },
            { "[]", false },
            { "\"move\"", false },
            { "null", false },
            { """{"type":1}""", false },
            { """{"type":"init"}""", false },
            { """{"type":"resign","v":1}""", true },
            { """{"type":"resign","v":1,"reason":"lost"}""", false },
            { """{"type":"resign"}""", false },
            { Info("{}"), true },
            { Info("null"), false },
            { Info("[]"), false },
            { Info("""{"unknown":1}"""), false },
            { """{"v":1,"move":"e2e4"}""", false },
        };

    [Theory]
    [MemberData(nameof(EdgeCases))]
    public void AgreesWithTheSchema(string line, bool valid) => Assert.Equal(valid, Accepts(line));

    public static TheoryData<string, string> ViolationLines() =>
        new()
        {
            { "{", "invalid_json" },
            { "", "invalid_json" },
            { """{"type":"move","v":NaN,"move":"e2e4"}""", "invalid_json" },
            { """{"type":"move","v":Infinity,"move":"e2e4"}""", "invalid_json" },
            { """{"type":"move","v":1} {}""", "invalid_json" },
            { new string('[', 100_000) + new string(']', 100_000), "schema_violation" },
            { Repeat("""{"a":""", 50_000) + "1" + new string('}', 50_000), "schema_violation" },
            {
                """{"type":"move","v":1""" + new string('0', 5000) + ""","move":"e2e4"}""",
                "schema_violation"
            },
            { """{"type":"move","v":1e400,"move":"e2e4"}""", "schema_violation" },
            { """{"type":"draw","v":1}""", "unknown_type" },
            { """{"type":"init"}""", "unknown_type" },
            { """{"type":"ready","v":2,"sdk":"1.0.0","lang":"python"}""", "unsupported_version" },
            { """{"type":"ready","v":"2","sdk":"1.0.0","lang":"python"}""", "schema_violation" },
            { """{"type":"move","v":2,"move":"e2e4"}""", "schema_violation" },
        };

    [Theory]
    [MemberData(nameof(ViolationLines))]
    public void ViolationCodes(string line, string code) =>
        CheckViolation(Encoding.UTF8.GetBytes(line), code);

    [Fact]
    public void InvalidUtf8IsInvalidJson() => CheckViolation([0xff, 0xfe], "invalid_json");

    [Fact]
    public void MessagesAreRead()
    {
        Assert.Equal(
            new ReadyMessage("1.0.0", "python"),
            Read("""{"type":"ready","v":1.0,"sdk":"1.0.0","lang":"python"}""")
        );
        Assert.Equal(new ResignMessage(), Read("""{"type":"resign","v":1}"""));
        Assert.Equal(new MoveMessage("e2e4"), Read(Move + "}"));
        var full = """{"depth":5.0,"seldepth":9,"score_mate":-3,"nodes":10,"pv":[],"text":"hi"}""";
        Assert.Equal(new MoveMessage("e2e4"), Read(Info(full)));
    }

    [Fact]
    public void DuplicateKeysUseTheLastValue() =>
        Assert.Equal(
            new MoveMessage("e2e4"),
            Read("""{"type":"move","v":1,"move":"zz","move":"e2e4"}""")
        );

    [Fact]
    public void ViolationMessagesNameTheField()
    {
        var error = Assert.Throws<ViolationException>(() => Read(Info("""{"depth":-1}""")));
        Assert.Equal("move: field 'info.depth' is not an integer in 0..1024", error.Message);
        error = Assert.Throws<ViolationException>(() => Read(Move + ""","b":1,"a":2}"""));
        Assert.Equal("move: unknown fields ['a', 'b']", error.Message);
    }

    private static void CheckViolation(byte[] line, string code)
    {
        var error = Assert.Throws<ViolationException>(() => BotMessages.Read(line));
        Assert.Equal(code, error.Code);
        Assert.True(error.Message.Length < 400, error.Message);
    }

    private static TheoryData<string> Examples(string kind)
    {
        var folder = Path.Combine(SpecFiles.Spec, "protocol", "v1", "examples", kind);
        return
        [
            .. Directory
                .EnumerateFiles(folder, "*.json")
                .Where(path =>
                    Prefixes.Any(prefix =>
                        Path.GetFileName(path).StartsWith(prefix, StringComparison.Ordinal)
                    )
                )
                .Order(StringComparer.Ordinal),
        ];
    }

    private static BotMessage Read(string line) => BotMessages.Read(Encoding.UTF8.GetBytes(line));

    private static bool Accepts(string line)
    {
        try
        {
            Read(line);
            return true;
        }
        catch (ViolationException)
        {
            return false;
        }
    }

    private static string Info(string info) => $"{Move},\"info\":{info}}}";

    private static string Ready(string sdk) =>
        $$"""{"type":"ready","v":1,"sdk":"{{sdk}}","lang":"python"}""";

    private static string Repeat(string text, int count) =>
        string.Concat(Enumerable.Repeat(text, count));

    private static string Pv(int count) => string.Join(',', Enumerable.Repeat("\"e2e4\"", count));
}
