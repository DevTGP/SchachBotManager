namespace Sbm;

/// <summary>Game parameters from init, passed to <see cref="Bot.OnGameStart"/>.</summary>
/// <param name="GameId">Identifier of the game.</param>
/// <param name="Color">Own color, <see cref="Sbm.Color.White"/> or <see cref="Sbm.Color.Black"/>.</param>
/// <param name="OpponentName">Display name of the opponent.</param>
/// <param name="StartFen">Start position of the game.</param>
/// <param name="InitialTimeMs">Base thinking time per side.</param>
/// <param name="IncrementMs">Time added after each own move.</param>
/// <param name="StartupMs">Budget for start-up including OnGameStart.</param>
/// <param name="MemoryLimitMib">Fixed memory protection limit of the sandbox (A14).</param>
/// <param name="Discipline">Display name of the discipline.</param>
public sealed record GameInfo(
    string GameId,
    byte Color,
    string OpponentName,
    string StartFen,
    long InitialTimeMs,
    long IncrementMs,
    long StartupMs,
    int MemoryLimitMib,
    string Discipline
);
