using Sbm.Bots;
using Sbm.Runtime.Referee;

namespace Sbm.Runtime.Play;

/// <summary>
/// How the opponent of a local Sdk.Play is given, as in the local arena (E67, E68):
/// <list type="bullet">
/// <item>"random" or "material": a reference bot of the SDK; "./random" means a file.</item>
/// <item>A .py file: runs with python3 (python on Windows), a .dll file with dotnet.</item>
/// <item>Any other file: runs as a program.</item>
/// <item>Anything else: a command line, e.g. "java -jar bot.jar" or "./engine".</item>
/// </list>
/// A TCP bot ("tcp", "tcp:PORT") needs the arena; the caller rejects it with IsTcp.
/// </summary>
internal static class OpponentParser
{
    internal const int MaxNameLength = 64;

    /// <summary>Throws OpponentException.</summary>
    internal static Opponent Parse(string text)
    {
        switch (text.ToLowerInvariant())
        {
            case "random":
                return new ReferenceOpponent("random", () => new RandomBot(), nameof(RandomBot));
            case "material":
                return new ReferenceOpponent(
                    "material",
                    () => new MaterialBot(),
                    nameof(MaterialBot)
                );
        }
        var extension = Path.GetExtension(text).ToLowerInvariant();
        if (extension is ".py" or ".dll")
        {
            if (!File.Exists(text))
            {
                throw new OpponentException($"{PyText.Repr(text)} is not a file");
            }
            var program = extension == ".py" ? PythonProgram() : "dotnet";
            return new ProcessOpponent(Stem(text), program, [Path.GetFullPath(text)]);
        }
        if (File.Exists(text))
        {
            return new ProcessOpponent(Stem(text), Path.GetFullPath(text), []);
        }
        return Command(text);
    }

    /// <summary>Whether the text names a bot that connects over TCP.</summary>
    internal static bool IsTcp(string text) =>
        text.Equals("tcp", StringComparison.OrdinalIgnoreCase)
        || text.StartsWith("tcp:", StringComparison.OrdinalIgnoreCase);

    /// <summary>Equal names get a number, e.g. for a bot against itself.</summary>
    internal static IReadOnlyList<string> UniqueNames(IReadOnlyList<string> names)
    {
        var unique = new List<string>(names.Count);
        for (var index = 0; index < names.Count; index++)
        {
            var name = names[index];
            if (names.Count(other => other == name) > 1)
            {
                var suffix = $"-{index + 1}";
                name = PyText.Prefix(name, MaxNameLength - suffix.Length) + suffix;
            }
            unique.Add(name);
        }
        return unique;
    }

    /// <summary>The name shown in the game: 1 to 64 characters.</summary>
    internal static string Shorten(string name) =>
        PyText.Prefix(name, MaxNameLength) is { Length: > 0 } shortened ? shortened : "bot";

    private static ProcessOpponent Command(string text)
    {
        IReadOnlyList<string> words;
        try
        {
            words = CommandLine.Split(text, posix: !OperatingSystem.IsWindows());
        }
        catch (FormatException error)
        {
            throw new OpponentException(
                $"cannot read the command {PyText.Repr(text)}: {error.Message}"
            );
        }
        if (words.Count == 0)
        {
            throw new OpponentException("the bot is empty");
        }
        return new ProcessOpponent(Shorten(NameFrom(words)), words[0], [.. words.Skip(1)]);
    }

    /// <summary>The first word naming a file after the program, e.g. bot for "java -jar bot.jar".</summary>
    private static string NameFrom(IReadOnlyList<string> words)
    {
        foreach (var word in words.Skip(1))
        {
            if (Path.HasExtension(word) && File.Exists(word))
            {
                return Path.GetFileNameWithoutExtension(word);
            }
        }
        return Path.GetFileNameWithoutExtension(words[0]) is { Length: > 0 } stem ? stem : words[0];
    }

    private static string Stem(string path) => Shorten(Path.GetFileNameWithoutExtension(path));

    private static string PythonProgram() => OperatingSystem.IsWindows() ? "python" : "python3";
}
