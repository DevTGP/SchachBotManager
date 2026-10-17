using Sbm.Runtime;

namespace Sbm.Tests.Runtime;

/// <summary>Start options from the command line and environment (E61).</summary>
public class OptionsParserTests
{
    private static Options Parse(string[] args, Dictionary<string, string>? env = null) =>
        OptionsParser.Parse(args, name => env?.GetValueOrDefault(name));

    [Fact]
    public void Defaults() =>
        Assert.Equal(
            new Options
            {
                Transport = Transport.Stdio,
                Port = Options.DefaultPort,
                LogLevel = LogLevel.Info,
                LogFile = null,
            },
            Parse([])
        );

    [Fact]
    public void Environment()
    {
        var env = new Dictionary<string, string>
        {
            ["SBM_TRANSPORT"] = "TCP",
            ["SBM_PORT"] = "9000",
            ["SBM_LOG_LEVEL"] = "debug",
            ["SBM_LOG_FILE"] = "bot.log",
        };
        Assert.Equal(
            new Options
            {
                Transport = Transport.Tcp,
                Port = 9000,
                LogLevel = LogLevel.Debug,
                LogFile = "bot.log",
            },
            Parse([], env)
        );
    }

    [Fact]
    public void ArgumentsWinOverEnvironment()
    {
        var env = new Dictionary<string, string>
        {
            ["SBM_PORT"] = "9000",
            ["SBM_LOG_LEVEL"] = "debug",
            ["SBM_LOG_FILE"] = "env.log",
        };
        string[] args = ["--tcp", "7000", "--log-level=Off", "--log-file", "arg.log"];
        Assert.Equal(
            new Options
            {
                Transport = Transport.Tcp,
                Port = 7000,
                LogLevel = LogLevel.Off,
                LogFile = "arg.log",
            },
            Parse(args, env)
        );
    }

    [Fact]
    public void LastOccurrenceWins() =>
        Assert.Equal(LogLevel.Error, Parse(["--log-level", "warn", "--log-level=error"]).LogLevel);

    [Fact]
    public void TcpWithoutPort()
    {
        Assert.Equal(new Options { Transport = Transport.Tcp }, Parse(["--tcp"]));
        Assert.Equal(9000, Parse(["--tcp"], new() { ["SBM_PORT"] = "9000" }).Port);
        Assert.Equal(Options.DefaultPort, Parse(["--tcp", "--log-level", "warn"]).Port);
        Assert.Equal(7000, Parse(["--tcp=7000"]).Port);
    }

    [Fact]
    public void OtherArgumentsBelongToTheBot() =>
        Assert.Equal(
            new Options { LogLevel = LogLevel.Error },
            Parse(["--depth", "4", "book.bin", "--log-level", "error", "-v"])
        );

    [Fact]
    public void DoubleDashEndsTheOptions() =>
        Assert.Equal(new Options(), Parse(["--", "--tcp", "--log-level", "loud"]));

    [Fact]
    public void EmptyLogFileMeansNone()
    {
        Assert.Null(Parse([], new() { ["SBM_LOG_FILE"] = "" }).LogFile);
        Assert.Null(Parse(["--log-file="], new() { ["SBM_LOG_FILE"] = "bot.log" }).LogFile);
    }

    [Fact]
    public void RemoteOptionsTakeTheirValues()
    {
        string[] args =
        [
            "--remote",
            "https://example.org",
            "--token",
            "t",
            "--opponent",
            "-1",
            "--tcp",
        ];
        var options = Parse(args);
        Assert.Equal(Transport.Remote, options.Transport);
        Assert.Equal(new RemoteOptions("https://example.org", "t", "-1"), options.Remote);
    }

    [Fact]
    public void RemoteFromArgumentsAndEnvironment()
    {
        string[] args =
        [
            "--remote",
            "https://example.org",
            "--opponent",
            "Material",
            "--time",
            "30+0.5",
        ];
        var options = Parse(args, new() { ["SBM_TOKEN"] = "t", ["SBM_COLOR"] = "Black" });
        Assert.Equal(
            new RemoteOptions("https://example.org", "t", "Material")
            {
                Color = "black",
                Time = "30+0.5",
            },
            options.Remote
        );
    }

    [Fact]
    public void RemoteThroughTheEnvironmentAlone()
    {
        var env = new Dictionary<string, string>
        {
            ["SBM_TRANSPORT"] = "remote",
            ["SBM_REMOTE_URL"] = "https://example.org",
            ["SBM_TOKEN"] = "t",
            ["SBM_OPPONENT"] = "Random",
            ["SBM_DISCIPLINE"] = "Blitz",
            ["SBM_TIME"] = "",
        };
        Assert.Equal(
            new RemoteOptions("https://example.org", "t", "Random") { Discipline = "Blitz" },
            Parse([], env).Remote
        );
    }

    [Fact]
    public void RemoteNamesAreLeftToTheBotOtherwise() =>
        Assert.Null(Parse(["--color", "red", "--time", "x"]).Remote);

    public static TheoryData<string[], string> IncompleteRemote() =>
        new()
        {
            {
                ["--remote", "https://example.org", "--opponent", "M"],
                "a remote game needs SBM_TOKEN"
            },
            {
                ["--remote", "https://example.org", "--token", "t"],
                "a remote game needs --opponent"
            },
            {
                ["--remote=", "--token", "t", "--opponent", "M"],
                "a remote game needs --remote URL"
            },
            {
                [
                    "--remote",
                    "https://example.org",
                    "--token",
                    "t",
                    "--opponent",
                    "M",
                    "--color",
                    "red",
                ],
                "invalid color 'red', expected one of white, black, random"
            },
        };

    [Theory]
    [MemberData(nameof(IncompleteRemote))]
    public void IncompleteRemoteOptions(string[] args, string message) =>
        Assert.Equal(message, Assert.Throws<OptionsException>(() => Parse(args)).Message);

    public static TheoryData<string[], string, string, string> InvalidValues() =>
        new()
        {
            { ["--tcp", "0"], "", "", "invalid port '0'" },
            { ["--tcp", "65536"], "", "", "invalid port '65536'" },
            { ["--tcp", "port"], "", "", "invalid port 'port'" },
            { ["--log-level", "loud"], "", "", "invalid log level 'loud'" },
            { ["--log-level"], "", "", "argument --log-level: expected one argument" },
            { ["--log-file", "--tcp"], "", "", "argument --log-file: expected one argument" },
            { [], "SBM_TRANSPORT", "udp", "invalid SBM_TRANSPORT 'udp'" },
            { [], "SBM_PORT", "-1", "invalid port '-1'" },
            { [], "SBM_PORT", "+80", "invalid port '+80'" },
            { [], "SBM_LOG_LEVEL", "5", "invalid log level '5'" },
        };

    [Theory]
    [MemberData(nameof(InvalidValues))]
    public void InvalidValuesAreErrors(string[] args, string name, string value, string message)
    {
        var env = name.Length == 0 ? null : new Dictionary<string, string> { [name] = value };
        var error = Assert.Throws<OptionsException>(() => Parse(args, env));
        Assert.StartsWith(message, error.Message, StringComparison.Ordinal);
    }
}
