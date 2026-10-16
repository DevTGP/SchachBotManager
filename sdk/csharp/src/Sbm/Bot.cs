namespace Sbm;

/// <summary>
/// Base class of every bot: override <see cref="ChooseMove"/>, optionally
/// <see cref="OnGameStart"/> and <see cref="OnGameEnd"/>, and start it with
/// <see cref="Sdk.Run{TBot}"/>. Fields of the object keep their values from turn to turn.
/// </summary>
public abstract class Bot
{
    private Info? _report;

    /// <summary>Called once before the first turn, within the start-up budget.</summary>
    public virtual void OnGameStart(GameInfo info) { }

    /// <summary>
    /// The move to play in the position on board, or <see cref="Move.Resign"/>. The bot may make
    /// and undo moves on board freely; the SDK keeps its own game position.
    /// </summary>
    public abstract Move ChooseMove(Board board, Clock clock);

    /// <summary>Called after game_over for cleanup and last log lines.</summary>
    public virtual void OnGameEnd(GameResult result) { }

    /// <summary>
    /// Sets the search information sent with the move of the current turn; also from another
    /// thread of the bot.
    /// </summary>
    public void Report(Info info)
    {
        ArgumentNullException.ThrowIfNull(info);
        Interlocked.Exchange(ref _report, info);
    }

    /// <summary>The info reported during the turn; nothing carries over to the next one.</summary>
    internal Info? TakeReport() => Interlocked.Exchange(ref _report, null);
}
