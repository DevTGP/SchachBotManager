namespace Sbm.Runtime.Referee;

/// <summary>
/// Remaining time of both sides in wall-clock time (E19, match-runner.md); the time of a turn
/// runs from sending turn to receiving move. Times are monotonic nanoseconds from the caller. A
/// turn may exceed the remaining time by the tolerance, which covers the transport; the
/// remaining time then becomes 0 before the increment is added.
/// </summary>
internal sealed class GameClock(MatchSettings settings)
{
    internal const long NanosecondsPerMs = 1_000_000;

    private readonly long[] _remainingMs = [settings.InitialTimeMs, settings.InitialTimeMs];

    /// <summary>False if the clock is switched off: no deadlines, no time is deducted.</summary>
    internal bool Running => settings.Clock;

    internal long RemainingMs(byte color) => _remainingMs[color];

    /// <summary>The latest moment for the answer to a turn sent at startNs.</summary>
    internal long? DeadlineNs(byte color, long startNs) =>
        Running ? startNs + (_remainingMs[color] + settings.ToleranceMs) * NanosecondsPerMs : null;

    /// <summary>The turn took longer than the remaining time plus the tolerance.</summary>
    internal bool IsOver(byte color, long elapsedMs) =>
        Running && elapsedMs > _remainingMs[color] + settings.ToleranceMs;

    /// <summary>Deducts a completed turn within the time and adds the increment.</summary>
    internal void Charge(byte color, long elapsedMs)
    {
        if (!Running)
        {
            return;
        }
        if (IsOver(color, elapsedMs))
        {
            throw new InvalidOperationException(
                $"a turn of {elapsedMs} ms is over the time; score a timeout"
            );
        }
        var remaining = Math.Max(_remainingMs[color] - elapsedMs, 0);
        _remainingMs[color] = remaining + settings.IncrementMs;
    }

    /// <summary>The side ran out of time.</summary>
    internal void Flag(byte color) => _remainingMs[color] = 0;

    /// <summary>Whole milliseconds between two monotonic times, rounded down.</summary>
    internal static long ElapsedMs(long startNs, long endNs)
    {
        var (quotient, remainder) = Math.DivRem(endNs - startNs, NanosecondsPerMs);
        return remainder < 0 ? quotient - 1 : quotient;
    }
}
