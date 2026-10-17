using Sbm.Bots;
using Sbm.Runtime.Play;

namespace Sbm.Tests.Runtime.Play;

/// <summary>How the opponent of a local Sdk.Play is given (E68, E120).</summary>
public sealed class OpponentParserTests : IDisposable
{
    private readonly DirectoryInfo _folder = Directory.CreateTempSubdirectory("sbm-opponent-");

    public void Dispose() => _folder.Delete(recursive: true);

    [Theory]
    [InlineData("random", typeof(RandomBot))]
    [InlineData("Material", typeof(MaterialBot))]
    public void ReferenceBots(string text, Type type)
    {
        var opponent = Assert.IsType<ReferenceOpponent>(OpponentParser.Parse(text));
        Assert.Equal(text.ToLowerInvariant(), opponent.Name);
        Assert.Equal(type.Name, opponent.ClassName);
        Assert.IsType(type, opponent.Create());
    }

    [Fact]
    public void APythonFileRunsWithPython()
    {
        var path = File("other.py");
        var opponent = Assert.IsType<ProcessOpponent>(OpponentParser.Parse(path));
        Assert.Equal("other", opponent.Name);
        Assert.Equal(OperatingSystem.IsWindows() ? "python" : "python3", opponent.Program);
        Assert.Equal([path], opponent.Arguments);
    }

    [Fact]
    public void ADllRunsWithDotnet()
    {
        var path = File("Engine.dll");
        var opponent = Assert.IsType<ProcessOpponent>(OpponentParser.Parse(path));
        Assert.Equal(("Engine", "dotnet"), (opponent.Name, opponent.Program));
        Assert.Equal([path], opponent.Arguments);
    }

    [Fact]
    public void AnotherFileIsTheProgram()
    {
        var path = File("random");
        var opponent = Assert.IsType<ProcessOpponent>(OpponentParser.Parse(path));
        Assert.Equal(("random", path), (opponent.Name, opponent.Program));
        Assert.Empty(opponent.Arguments);
    }

    [Theory]
    [InlineData("missing.py")]
    [InlineData("missing.DLL")]
    public void AMissingBotFile(string name)
    {
        var path = Path.Combine(_folder.FullName, name);
        var error = Assert.Throws<OpponentException>(() => OpponentParser.Parse(path));
        Assert.EndsWith("is not a file", error.Message, StringComparison.Ordinal);
    }

    [Fact]
    public void ACommandIsNamedAfterItsFile()
    {
        var jar = File("bot.jar");
        var opponent = Assert.IsType<ProcessOpponent>(
            OpponentParser.Parse($"java -Xmx1g -jar \"{jar}\"")
        );
        Assert.Equal(("bot", "java"), (opponent.Name, opponent.Program));
        Assert.Equal(["-Xmx1g", "-jar", jar], opponent.Arguments);
    }

    [Fact]
    public void ACommandWithoutAFileIsNamedAfterTheProgram()
    {
        var opponent = Assert.IsType<ProcessOpponent>(OpponentParser.Parse("engine --depth 3"));
        Assert.Equal(("engine", "engine"), (opponent.Name, opponent.Program));
    }

    [Theory]
    [InlineData("\"open")]
    [InlineData("  ")]
    public void UnreadableCommands(string text) =>
        Assert.Throws<OpponentException>(() => OpponentParser.Parse(text));

    [Theory]
    [InlineData("tcp", true)]
    [InlineData("TCP:7470", true)]
    [InlineData("tcpbot", false)]
    [InlineData("random", false)]
    public void TcpBots(string text, bool tcp) => Assert.Equal(tcp, OpponentParser.IsTcp(text));

    [Fact]
    public void EqualNamesGetANumber()
    {
        Assert.Equal(["a", "b"], OpponentParser.UniqueNames(["a", "b"]));
        Assert.Equal(["a-1", "a-2"], OpponentParser.UniqueNames(["a", "a"]));
        var long64 = new string('x', 64);
        var unique = OpponentParser.UniqueNames([long64, long64]);
        Assert.Equal([new string('x', 62) + "-1", new string('x', 62) + "-2"], unique);
    }

    [Fact]
    public void NamesAreShortened()
    {
        Assert.Equal(new string('ä', 64), OpponentParser.Shorten(new string('ä', 70)));
        Assert.Equal("bot", OpponentParser.Shorten(""));
        Assert.Equal("MyBot", OpponentParser.Shorten("MyBot"));
    }

    private string File(string name)
    {
        var path = Path.Combine(_folder.FullName, name);
        System.IO.File.WriteAllText(path, "");
        return path;
    }
}
