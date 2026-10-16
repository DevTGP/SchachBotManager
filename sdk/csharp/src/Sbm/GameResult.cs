namespace Sbm;

/// <summary>End of the game from game_over, passed to <see cref="Bot.OnGameEnd"/>.</summary>
/// <param name="Result">1-0, 0-1, 1/2-1/2 or * (aborted).</param>
/// <param name="Termination">Termination code as listed in the protocol (E44).</param>
public sealed record GameResult(string Result, string Termination);
