using System.Globalization;
using System.Text.RegularExpressions;

namespace Sbm.Runtime;

/// <summary>Time controls as written on the command line and in PGN: seconds plus increment, "60+1".</summary>
internal static partial class TimeControl
{
    /// <summary>
    /// Initial time and increment in milliseconds; seconds may have up to three decimals. Throws
    /// FormatException with a message for the author.
    /// </summary>
    internal static (long InitialMs, long IncrementMs) Parse(string text)
    {
        var match = Pattern().Match(text.Trim());
        if (!match.Success)
        {
            throw Invalid(text);
        }
        var initial = Milliseconds(match.Groups[1].Value, text);
        var increment = match.Groups[2].Success ? Milliseconds(match.Groups[2].Value, text) : 0;
        if (initial == 0)
        {
            throw new FormatException("the initial time must be more than 0 seconds");
        }
        return (initial, increment);
    }

    private static long Milliseconds(string seconds, string text)
    {
        try
        {
            return (long)(decimal.Parse(seconds, CultureInfo.InvariantCulture) * 1000);
        }
        catch (OverflowException)
        {
            throw Invalid(text);
        }
    }

    private static FormatException Invalid(string text) =>
        new($"invalid time control '{text}', expected seconds+increment such as 60+1 or 0.5");

    [GeneratedRegex(@"^([0-9]+(?:\.[0-9]{1,3})?)(?:\+([0-9]+(?:\.[0-9]{1,3})?))?$")]
    private static partial Regex Pattern();
}
