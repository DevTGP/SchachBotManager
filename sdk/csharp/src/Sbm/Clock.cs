using System.Diagnostics;

namespace Sbm;

/// <summary>
/// Time situation of the current turn; the referee's clock is authoritative. Elapsed time is
/// measured with a monotonic clock from the creation of the object, which the SDK does right
/// after receiving turn.
/// </summary>
public sealed class Clock
{
    private readonly long _start = Stopwatch.GetTimestamp();
    private readonly long _remainingMs;
    private readonly long _opponentRemainingMs;
    private readonly long _incrementMs;

    /// <summary>A clock whose elapsed time starts now, e.g. for tests of a bot.</summary>
    public Clock(long remainingMs, long opponentRemainingMs, long incrementMs)
    {
        _remainingMs = remainingMs;
        _opponentRemainingMs = opponentRemainingMs;
        _incrementMs = incrementMs;
    }

    /// <summary>Own remaining time at the start of this turn; does not decrease while thinking.</summary>
    public long RemainingMs() => _remainingMs;

    /// <summary>Remaining time of the opponent.</summary>
    public long OpponentRemainingMs() => _opponentRemainingMs;

    /// <summary>Time added after each own move.</summary>
    public long IncrementMs() => _incrementMs;

    /// <summary>Time spent on this turn so far; keep a margin for the transport.</summary>
    public long ElapsedMs() =>
        Stopwatch.GetElapsedTime(_start).Ticks / TimeSpan.TicksPerMillisecond;

    /// <inheritdoc/>
    public override string ToString() =>
        $"Clock(remainingMs={_remainingMs}, opponentRemainingMs={_opponentRemainingMs}, "
        + $"incrementMs={_incrementMs})";
}
