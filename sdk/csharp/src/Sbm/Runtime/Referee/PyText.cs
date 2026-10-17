using System.Globalization;
using System.Text;

namespace Sbm.Runtime.Referee;

/// <summary>
/// Text as the Python SDK measures and prints it in referee messages: lengths in code points
/// (a lone surrogate counts as one) and repr() for quoted values.
/// </summary>
internal static class PyText
{
    /// <summary>The number of code points.</summary>
    internal static int Length(string text) => CodePointsOf(text).Count();

    /// <summary>The first count code points.</summary>
    internal static string Prefix(string text, int count)
    {
        var result = new StringBuilder();
        foreach (var codePoint in CodePointsOf(text).Take(count))
        {
            Append(result, codePoint);
        }
        return result.ToString();
    }

    /// <summary>Python's repr of a str, e.g. 'name' or "it's".</summary>
    internal static string Repr(string text)
    {
        var quote =
            text.Contains('\'', StringComparison.Ordinal)
            && !text.Contains('"', StringComparison.Ordinal)
                ? '"'
                : '\'';
        var result = new StringBuilder().Append(quote);
        foreach (var codePoint in CodePointsOf(text))
        {
            switch (codePoint)
            {
                case '\\':
                    result.Append(@"\\");
                    break;
                case '\t':
                    result.Append(@"\t");
                    break;
                case '\n':
                    result.Append(@"\n");
                    break;
                case '\r':
                    result.Append(@"\r");
                    break;
                default:
                    if (codePoint == quote)
                    {
                        result.Append('\\').Append(quote);
                    }
                    else if (IsPrintable(codePoint))
                    {
                        Append(result, codePoint);
                    }
                    else
                    {
                        result.Append(Escape(codePoint));
                    }
                    break;
            }
        }
        return result.Append(quote).ToString();
    }

    /// <summary>Python's repr of a list of str, e.g. ['a', 'b'].</summary>
    internal static string Repr(IEnumerable<string> texts) =>
        $"[{string.Join(", ", texts.Select(Repr))}]";

    private static string Escape(int codePoint) =>
        codePoint switch
        {
            < 0x100 => $"\\x{codePoint:x2}",
            < 0x10000 => $"\\u{codePoint:x4}",
            _ => $"\\U{codePoint:x8}",
        };

    private static bool IsPrintable(int codePoint)
    {
        if (codePoint == ' ')
        {
            return true;
        }
        var category = codePoint is >= 0xD800 and <= 0xDFFF
            ? UnicodeCategory.Surrogate
            : CharUnicodeInfo.GetUnicodeCategory(codePoint);
        return category
            is not (
                UnicodeCategory.Control
                or UnicodeCategory.Format
                or UnicodeCategory.Surrogate
                or UnicodeCategory.PrivateUse
                or UnicodeCategory.OtherNotAssigned
                or UnicodeCategory.LineSeparator
                or UnicodeCategory.ParagraphSeparator
                or UnicodeCategory.SpaceSeparator
            );
    }

    private static void Append(StringBuilder result, int codePoint)
    {
        if (codePoint is >= 0xD800 and <= 0xDFFF)
        {
            result.Append((char)codePoint);
        }
        else
        {
            result.Append(char.ConvertFromUtf32(codePoint));
        }
    }

    private static IEnumerable<int> CodePointsOf(string text)
    {
        for (var index = 0; index < text.Length; index++)
        {
            if (
                char.IsHighSurrogate(text[index])
                && index + 1 < text.Length
                && char.IsLowSurrogate(text[index + 1])
            )
            {
                yield return char.ConvertToUtf32(text[index], text[index + 1]);
                index++;
            }
            else
            {
                yield return text[index];
            }
        }
    }
}
