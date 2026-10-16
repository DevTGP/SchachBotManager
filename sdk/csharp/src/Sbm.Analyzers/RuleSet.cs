using System.Globalization;

namespace Sbm.Analyzers;

/// <summary>The whitelist of uploaded bots, read from csharp_rules.txt (E203).</summary>
public sealed class RuleSet
{
    private const string ResourceName = "Sbm.Analyzers.csharp_rules.txt";

    private static readonly Lazy<RuleSet> DefaultRules = new(LoadDefault);

    private readonly HashSet<string> _namespaces = new(StringComparer.Ordinal);
    private readonly HashSet<string> _types = new(StringComparer.Ordinal);
    private readonly HashSet<string> _forbidden = new(StringComparer.Ordinal);
    private readonly HashSet<string> _assemblies = new(StringComparer.Ordinal);

    private RuleSet() { }

    /// <summary>The rules shipped with this assembly.</summary>
    public static RuleSet Default => DefaultRules.Value;

    /// <summary>Name of the rules in the verification report, e.g. csharp-1.</summary>
    public string Name { get; private set; } = "";

    /// <summary>Assemblies the compiled bot may reference.</summary>
    public IReadOnlyCollection<string> Assemblies => _assemblies;

    /// <summary>Parses the line format described in csharp_rules.txt.</summary>
    /// <exception cref="FormatException">A line is not one of the known entries.</exception>
    public static RuleSet Parse(string text)
    {
        var rules = new RuleSet();
        var number = 0;
        foreach (var raw in text.Split('\n'))
        {
            number++;
            var line = raw.Trim();
            if (line.Length == 0 || line[0] == '#')
            {
                continue;
            }
            var parts = line.Split((char[]?)null, StringSplitOptions.RemoveEmptyEntries);
            if (parts.Length != 2)
            {
                throw new FormatException(Invalid(number, line));
            }
            var target = parts[0] switch
            {
                "namespace" => rules._namespaces,
                "type" => rules._types,
                "forbid" => rules._forbidden,
                "assembly" => rules._assemblies,
                "ruleset" => null,
                _ => throw new FormatException(Invalid(number, line)),
            };
            if (target is null)
            {
                rules.Name = parts[1];
            }
            else
            {
                target.Add(parts[1]);
            }
        }
        if (rules.Name.Length == 0)
        {
            throw new FormatException("the rules have no ruleset line");
        }
        return rules;
    }

    /// <summary>Whether a type outside the bot may be used.</summary>
    /// <param name="ns">Its namespace, empty for the global namespace.</param>
    /// <param name="name">Its name without arity; for a nested type that of the outermost type.</param>
    public bool AllowsType(string ns, string name)
    {
        var full = ns.Length == 0 ? name : ns + "." + name;
        return !_forbidden.Contains(full) && (_types.Contains(full) || _namespaces.Contains(ns));
    }

    /// <summary>Whether a member of an allowed type is forbidden on its own.</summary>
    /// <param name="type">Full name of the type without arity.</param>
    /// <param name="member">Name of the member.</param>
    public bool ForbidsMember(string type, string member) =>
        _forbidden.Contains(type + "." + member);

    private static string Invalid(int number, string line) =>
        string.Format(CultureInfo.InvariantCulture, "line {0}: invalid entry '{1}'", number, line);

    private static RuleSet LoadDefault()
    {
        using var stream =
            typeof(RuleSet).Assembly.GetManifestResourceStream(ResourceName)
            ?? throw new InvalidOperationException("the rules are missing from the assembly");
        using var reader = new StreamReader(stream);
        return Parse(reader.ReadToEnd());
    }
}
