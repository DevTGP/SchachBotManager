using System.Globalization;
using System.Numerics;

namespace Sbm.Runtime.Referee;

/// <summary>A JSON number as written, so that integers of any length keep their value.</summary>
internal sealed record NumberText(string Text)
{
    // Longer integers cannot fit any field; they are read as floating point like in Python.
    private const int MaxIntegerDigits = 64;

    /// <summary>The value as a JSON Schema integer: 3 and 3.0 count, 3.5 and 1e400 do not.</summary>
    internal BigInteger? Integer()
    {
        if (Text.Length <= MaxIntegerDigits && Text.IndexOfAny(['.', 'e', 'E']) < 0)
        {
            return BigInteger.Parse(
                Text,
                NumberStyles.AllowLeadingSign,
                CultureInfo.InvariantCulture
            );
        }
        var value = double.Parse(Text, NumberStyles.Float, CultureInfo.InvariantCulture);
        return double.IsFinite(value) && Math.Floor(value) == value ? new BigInteger(value) : null;
    }
}
