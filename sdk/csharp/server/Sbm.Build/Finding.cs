namespace Sbm.Build;

/// <summary>
/// A problem with the bot as the runner reads it (statische-analyse.md): rule, file relative to
/// the bot's folder (empty for the program as a whole), 1-based line if known, message.
/// </summary>
internal sealed record Finding(string Rule, string File, int? Line, string Message);

/// <summary>The findings of one stage, at most <see cref="Limit"/> of them.</summary>
internal sealed class Section
{
    public const int Limit = 100;

    public Section(IEnumerable<Finding> findings)
    {
        var ordered = findings
            .Distinct()
            .OrderBy(finding => finding.File, StringComparer.Ordinal)
            .ThenBy(finding => finding.Line ?? 0)
            .ThenBy(finding => finding.Rule, StringComparer.Ordinal)
            .ThenBy(finding => finding.Message, StringComparer.Ordinal)
            .ToList();
        Truncated = ordered.Count > Limit;
        Findings = ordered.Take(Limit).ToList();
    }

    public IReadOnlyList<Finding> Findings { get; }

    public bool Truncated { get; }

    public bool Ok => Findings.Count == 0;
}
