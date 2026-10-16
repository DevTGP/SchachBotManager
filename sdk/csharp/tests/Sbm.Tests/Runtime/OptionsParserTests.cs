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
        var options = Parse(["--remote", "https://example.org", "--opponent", "-1", "--tcp"]);
        Assert.Equal(Transport.Remote, options.Transport);
    }

    public static TheoryData<string[], string, string, string> InvalidValues() =>
        new()
        {
            { ["--tcp", "0"], "", "", "invalid port '0'" },
            { ["--tcp", "65536"], "", "", "invalid port '65536'" },
            { ["--tcp", "port"], "", "", "invalid port 'port'" },
            { ["--log-level", "loud"], "", "", "invalid log level 'loud'" },
            { ["--log-level"], "", "", "argument --log-level: expected one argument" },
            { ["--log-file", "--tcp"], "", "", "argument --log-file: expected one argument" },
            { [], "SBM_TRANSPORT", "remote", "invalid SBM_TRANSPORT 'remote'" },
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
