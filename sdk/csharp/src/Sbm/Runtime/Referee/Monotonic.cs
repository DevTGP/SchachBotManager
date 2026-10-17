using System.Diagnostics;

namespace Sbm.Runtime.Referee;

/// <summary>A monotonic clock in nanoseconds, the time base of the referee.</summary>
internal static class Monotonic
{
    internal static long Now() =>
        (long)(Stopwatch.GetTimestamp() * (1_000_000_000.0 / Stopwatch.Frequency));
}
