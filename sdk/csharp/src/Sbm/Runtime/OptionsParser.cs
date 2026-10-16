using System.Globalization;

namespace Sbm.Runtime;

/// <summary>
/// Reads the options like argparse in the Python SDK: <c>--name value</c> or <c>--name=value</c>,
/// the last occurrence wins, <c>--</c> ends the options, and unknown arguments belong to the
/// bot. Arguments win over the environment.
/// </summary>
internal static class OptionsParser
{
    private static readonly string[] LevelNames =
    [
        "TRACE",
        "DEBUG",
        "INFO",
        "WARN",
        "ERROR",
        "OFF",
    ];

    // Options of the remote transport (E116), read with a value so that it is not taken for an
    // argument of the bot; the transport itself follows in step 5 (E197).
    private static readonly string[] RemoteValues =
    [
        "--remote",
        "--token",
        "--opponent",
        "--color",
        "--discipline",
        "--time",
    ];

    internal static Options Parse(IReadOnlyList<string> args, Func<string, string?> env)
    {
        var options = FromEnvironment(env);
        var values = Arguments(args);
        if (values.TryGetValue("--tcp", out var tcp))
        {
            options = options with
            {
                Transport = Transport.Tcp,
                Port = string.IsNullOrEmpty(tcp) ? options.Port : Port(tcp),
            };
        }
        if (values.TryGetValue("--log-level", out var level))
        {
            options = options with { LogLevel = Level(level!) };
        }
        if (values.TryGetValue("--log-file", out var file))
        {
            options = options with { LogFile = string.IsNullOrEmpty(file) ? null : file };
        }
        if (values.ContainsKey("--remote"))
        {
            options = options with { Transport = Transport.Remote };
        }
        return options;
    }

    private static Options FromEnvironment(Func<string, string?> env)
    {
        var transport = (env("SBM_TRANSPORT") ?? "stdio").ToLowerInvariant();
        var port = env("SBM_PORT");
        var level = env("SBM_LOG_LEVEL");
        var file = env("SBM_LOG_FILE");
        return new Options
        {
            Transport = transport switch
            {
                "stdio" => Transport.Stdio,
                "tcp" => Transport.Tcp,
                _ => throw new OptionsException(
                    $"invalid SBM_TRANSPORT '{transport}', expected stdio or tcp"
                ),
            },
            Port = port is null ? Options.DefaultPort : Port(port),
            LogLevel = level is null ? LogLevel.Info : Level(level),
            LogFile = string.IsNullOrEmpty(file) ? null : file,
        };
    }

    /// <summary>The last value of each known option; --tcp without a value maps to "".</summary>
    private static Dictionary<string, string?> Arguments(IReadOnlyList<string> args)
    {
        var values = new Dictionary<string, string?>(StringComparer.Ordinal);
        for (var index = 0; index < args.Count; index++)
        {
            var argument = args[index];
            if (argument == "--")
            {
                break;
            }
            var equals = argument.IndexOf('=', StringComparison.Ordinal);
            var name = equals < 0 ? argument : argument[..equals];
            string? inline = equals < 0 ? null : argument[(equals + 1)..];
            if (name == "--tcp")
            {
                // An optional value: the next argument, unless it looks like an option.
                if (inline is null && index + 1 < args.Count && !args[index + 1].StartsWith('-'))
                {
                    inline = args[++index];
                }
                values[name] = inline ?? "";
            }
            else if (name is "--log-level" or "--log-file" || RemoteValues.Contains(name))
            {
                if (inline is null)
                {
                    if (index + 1 >= args.Count || IsOption(args[index + 1]))
                    {
                        throw new OptionsException($"argument {name}: expected one argument");
                    }
                    inline = args[++index];
                }
                values[name] = inline;
            }
        }
        return values;
    }

    /// <summary>Like argparse: "-" alone and negative numbers are values, not options.</summary>
    private static bool IsOption(string argument) =>
        argument.Length > 1
        && argument[0] == '-'
        && !double.TryParse(argument, NumberStyles.Float, CultureInfo.InvariantCulture, out _);

    private static int Port(string text) =>
        text.Length > 0
        && text.All(char.IsAsciiDigit)
        && int.TryParse(text, NumberStyles.None, CultureInfo.InvariantCulture, out var port)
        && port is >= 1 and <= 65535
            ? port
            : throw new OptionsException($"invalid port '{text}', expected 1 to 65535");

    private static byte Level(string text)
    {
        var index = Array.IndexOf(LevelNames, text.ToUpperInvariant());
        return index >= 0
            ? (byte)index
            : throw new OptionsException(
                $"invalid log level '{text}', expected one of {string.Join(", ", LevelNames)}"
            );
    }
}
