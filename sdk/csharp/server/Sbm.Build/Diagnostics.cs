using System.Globalization;
using Microsoft.CodeAnalysis;

namespace Sbm.Build;

/// <summary>Findings from Roslyn's diagnostics and locations.</summary>
internal static class Diagnostics
{
    public static Finding From(Diagnostic diagnostic) =>
        At(diagnostic.Id, diagnostic.Location, diagnostic.GetMessage(CultureInfo.InvariantCulture));

    /// <summary>
    /// The place in the file as written: #line directives cannot move a finding elsewhere,
    /// because the mapped position is not used.
    /// </summary>
    public static Finding At(string rule, Location location, string message)
    {
        if (!location.IsInSource)
        {
            return new Finding(rule, "", null, message);
        }
        var span = location.SourceTree!.GetLineSpan(location.SourceSpan);
        return new Finding(rule, span.Path, span.StartLinePosition.Line + 1, message);
    }
}
