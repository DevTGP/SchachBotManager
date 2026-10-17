using Sbm.Runtime.Play;

namespace Sbm.Tests.Runtime.Play;

/// <summary>Command lines of an opponent: POSIX like shlex, Windows with its backslashes.</summary>
public sealed class CommandLineTests
{
    public static TheoryData<string, string[]> Posix() =>
        new()
        {
            { "java -jar bot.jar", ["java", "-jar", "bot.jar"] },
            { "  a\t b\n", ["a", "b"] },
            { "", [] },
            { "'my bot' \"x y\"", ["my bot", "x y"] },
            { "a'b c'd", ["ab cd"] },
            { "''", [""] },
            { @"a\ b", ["a b"] },
            { @"'a\b'", [@"a\b"] },
            { @"""a\""b\\c\d""", [@"a""b\c\d"] },
        };

    public static TheoryData<string, string[]> Windows() =>
        new()
        {
            { @"C:\bots\engine.exe --fast", [@"C:\bots\engine.exe", "--fast"] },
            { @"""C:\My Bots\bot.exe"" x", [@"C:\My Bots\bot.exe", "x"] },
            { "'a b'", ["'a", "b'"] },
            { "\"\"", [""] },
        };

    [Theory]
    [MemberData(nameof(Posix))]
    public void PosixWords(string text, string[] words) =>
        Assert.Equal(words, CommandLine.Split(text, posix: true));

    [Theory]
    [MemberData(nameof(Windows))]
    public void WindowsWords(string text, string[] words) =>
        Assert.Equal(words, CommandLine.Split(text, posix: false));

    [Theory]
    [InlineData("'open", true, "No closing quotation")]
    [InlineData("\"open", true, "No closing quotation")]
    [InlineData("\"open", false, "No closing quotation")]
    [InlineData(@"end\", true, "No escaped character")]
    [InlineData(@"""end\", true, "No escaped character")]
    public void Errors(string text, bool posix, string message)
    {
        var error = Assert.Throws<FormatException>(() => CommandLine.Split(text, posix));
        Assert.Equal(message, error.Message);
    }
}
