// The names of the constants are their documentation; spec/api/constants.json has no more.
#pragma warning disable CS1591

namespace Sbm;

/// <summary>
/// Colors (E35). Values of the type Color in spec/api/constants.json.
/// </summary>
public static class Color
{
    public const byte White = 0;
    public const byte Black = 1;

    /// <summary>No color, e.g. both colors in Board.pieces.</summary>
    public const byte NoColor = 2;
}
