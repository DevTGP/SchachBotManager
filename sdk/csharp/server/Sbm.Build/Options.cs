using System.Text.RegularExpressions;

namespace Sbm.Build;

/// <summary>
/// The command line: sbm-build --entry CLASS --references DIR [--references DIR ...] BOT_DIR.
/// </summary>
internal sealed partial record Options(string Entry, IReadOnlyList<string> References, string Bot)
{
    public const string Usage =
        "usage: sbm-build --entry CLASS --references DIR [--references DIR ...] BOT_DIR";

    /// <summary>The options, or null with a message if the command line is not valid.</summary>
    public static Options? Parse(IReadOnlyList<string> args, out string error)
    {
        string? entry = null;
        string? bot = null;
        var references = new List<string>();
        for (var i = 0; i < args.Count; i++)
        {
            var arg = args[i];
            if (arg is "--entry" or "--references")
            {
                if (i + 1 == args.Count)
                {
                    error = $"{arg} needs a value";
                    return null;
                }
                if (arg == "--entry")
                {
                    entry = args[++i];
                }
                else
                {
                    references.Add(args[++i]);
                }
            }
            else if (arg.StartsWith('-') || bot is not null)
            {
                error = $"unexpected argument '{arg}'";
                return null;
            }
            else
            {
                bot = arg;
            }
        }
        if (entry is null || bot is null || references.Count == 0)
        {
            error = Usage;
            return null;
        }
        if (!ClassName().IsMatch(entry))
        {
            error = $"'{entry}' is not a class name";
            return null;
        }
        error = "";
        return new Options(entry, references, bot);
    }

    /// <summary>A full class name as the upload accepts it: Name or Namespace.Name.</summary>
    [GeneratedRegex(@"\A[A-Za-z_][A-Za-z0-9_]{0,99}(\.[A-Za-z_][A-Za-z0-9_]{0,99}){0,9}\z")]
    public static partial Regex ClassName();
}
