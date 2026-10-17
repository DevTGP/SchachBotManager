namespace Sbm.Runtime.Viewer;

/// <summary>
/// One game as Game sees it, passed to the viewer window if one is open (E106). The reference
/// bots of Sdk.Play run on muted threads and stay out of the window.
/// </summary>
internal static class GameView
{
    private static ViewerWindow? Window => Log.Muted ? null : ViewerWindow.Active;

    internal static void Started(string bot, GameInfo info) => Window?.GameStarted(bot, info);

    /// <summary>
    /// ply is the number of half-moves played including uci, which the first turn does not have;
    /// board is the position after it. The FEN is only computed for an open window.
    /// </summary>
    internal static void OpponentMoved(int ply, string? uci, Board board, Clock clock)
    {
        if (ply > 0 && uci is not null && Window is { } window)
        {
            var clocks = (clock.RemainingMs(), clock.OpponentRemainingMs());
            window.MovePlayed(ply, uci, board.Fen(), byBot: false, clocks);
        }
    }

    /// <summary>
    /// The move sent to the referee with its info as JSON text and the position after it; the
    /// bot's clock is an estimate.
    /// </summary>
    internal static void OwnMove(int ply, string uci, Board board, Clock clock, string? info)
    {
        if (Window is not { } window)
        {
            return;
        }
        var elapsedMs = clock.ElapsedMs();
        var remainingMs = clock.RemainingMs() - elapsedMs + clock.IncrementMs();
        var clocks = (remainingMs, clock.OpponentRemainingMs());
        window.MovePlayed(ply, uci, board.Fen(), byBot: true, clocks, elapsedMs, info);
    }

    internal static void Ended(System.Text.Json.JsonElement gameOver) => Window?.GameOver(gameOver);
}
