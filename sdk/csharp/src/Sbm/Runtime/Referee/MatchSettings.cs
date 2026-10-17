using System.Text.RegularExpressions;

namespace Sbm.Runtime.Referee;

/// <summary>
/// Everything the referee needs besides the two players; checked on creation (match-runner.md).
/// With clock false no deadline applies and the remaining times stay at the initial time.
/// maxMoves counts full moves; when it is reached without another ending, the game is drawn.
/// </summary>
internal sealed partial record MatchSettings
{
    internal const string StandardFen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1";

    private const long MaxMilliseconds = (1L << 53) - 1;
    private const int MaxNameLength = 64;

    /// <summary>Throws InvalidArgumentException for a value outside its range.</summary>
    internal MatchSettings(
        long initialTimeMs,
        long incrementMs = 0,
        long startupMs = 10_000,
        long toleranceMs = 20,
        long maxMoves = 500,
        string startFen = StandardFen,
        string gameId = "local",
        string discipline = "Local",
        long memoryLimitMib = 1024,
        bool clock = true
    )
    {
        CheckRange("initial_time_ms", initialTimeMs, 1);
        CheckRange("increment_ms", incrementMs, 0);
        CheckRange("startup_ms", startupMs, 1);
        CheckRange("tolerance_ms", toleranceMs, 0);
        CheckRange("max_moves", maxMoves, 1);
        CheckRange("memory_limit_mib", memoryLimitMib, 1);
        CheckGameId(gameId);
        CheckName("discipline", discipline);
        try
        {
            Board.FromFen(startFen);
        }
        catch (ChessException error)
        {
            throw new InvalidArgumentException($"start_fen: {error.Message}");
        }
        InitialTimeMs = initialTimeMs;
        IncrementMs = incrementMs;
        StartupMs = startupMs;
        ToleranceMs = toleranceMs;
        MaxMoves = maxMoves;
        StartFen = startFen;
        GameId = gameId;
        Discipline = discipline;
        MemoryLimitMib = memoryLimitMib;
        Clock = clock;
    }

    internal long InitialTimeMs { get; }

    internal long IncrementMs { get; }

    internal long StartupMs { get; }

    internal long ToleranceMs { get; }

    internal long MaxMoves { get; }

    internal string StartFen { get; }

    internal string GameId { get; private init; }

    internal string Discipline { get; }

    internal long MemoryLimitMib { get; }

    internal bool Clock { get; }

    /// <summary>The same settings for another game.</summary>
    internal MatchSettings WithGameId(string gameId)
    {
        CheckGameId(gameId);
        return this with { GameId = gameId };
    }

    /// <summary>Display names in init have 1 to 64 characters (common.schema.json).</summary>
    internal static void CheckName(string field, string name)
    {
        if (PyText.Length(name) is < 1 or > MaxNameLength)
        {
            throw new InvalidArgumentException(
                $"{field} {PyText.Repr(name)} must be a str of 1 to {MaxNameLength} characters"
            );
        }
    }

    private static void CheckGameId(string gameId)
    {
        if (!GameIdPattern().IsMatch(gameId))
        {
            throw new InvalidArgumentException(
                $"game_id {PyText.Repr(gameId)} must be 1 to 64 of A-Z a-z 0-9 _ -"
            );
        }
    }

    private static void CheckRange(string field, long value, long low)
    {
        if (value < low || value > MaxMilliseconds)
        {
            throw new InvalidArgumentException(
                $"{field}={value} is outside {low}..{MaxMilliseconds}"
            );
        }
    }

    [GeneratedRegex(@"\A[A-Za-z0-9_-]{1,64}\z")]
    private static partial Regex GameIdPattern();
}
