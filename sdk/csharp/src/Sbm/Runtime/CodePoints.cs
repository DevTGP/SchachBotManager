using System.Text;

namespace Sbm.Runtime;

/// <summary>Text limits of the protocols, which count code points like the Python SDK.</summary>
internal static class CodePoints
{
    /// <summary>At most max code points; lone surrogates, which have no UTF-8 form, become U+FFFD.</summary>
    internal static string Truncate(string text, int max)
    {
        var result = new StringBuilder();
        foreach (var rune in text.EnumerateRunes().Take(max))
        {
            result.Append(rune.ToString());
        }
        return result.ToString();
    }
}
