// The names of the constants are their documentation; spec/api/constants.json has no more.
#pragma warning disable CS1591

namespace Sbm;

/// <summary>
/// Levels of the debug log. Values of the type LogLevel in spec/api/constants.json.
/// </summary>
public static class LogLevel
{
    public const byte Trace = 0;
    public const byte Debug = 1;
    public const byte Info = 2;
    public const byte Warn = 3;
    public const byte Error = 4;
    public const byte Off = 5;
}
