namespace Sbm;

/// <summary>One game played with <see cref="Sdk.Play{TBot}"/>, from the own bot's point of view.</summary>
/// <param name="GameId">
/// Identifier of the game; on the server the match id, under which the site shows the game.
/// </param>
/// <param name="Color">Own color.</param>
/// <param name="OpponentName">Display name of the opponent.</param>
/// <param name="Result">1-0, 0-1, 1/2-1/2 or * (aborted).</param>
/// <param name="Termination">Termination code as listed in the protocol (E44).</param>
public sealed record PlayedGame(
    string GameId,
    byte Color,
    string OpponentName,
    string Result,
    string Termination
);
