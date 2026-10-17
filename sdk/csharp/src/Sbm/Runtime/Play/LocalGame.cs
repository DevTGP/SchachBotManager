using System.Runtime.ExceptionServices;
using Sbm.Runtime.Referee;

namespace Sbm.Runtime.Play;

/// <summary>One local game of Sdk.Play (E120): the own bot in a thread, the referee in this one.</summary>
internal static class LocalGame
{
    /// <summary>
    /// Throws the BotFailureException or ProtocolException that ended the own bot's side, after
    /// the game. number counts from 1 and makes the game id unique.
    /// </summary>
    internal static PlayedGame Play(
        Func<Bot> create,
        string botName,
        string name,
        Opponent opponent,
        byte color,
        MatchSettings settings,
        int number
    )
    {
        settings = settings.WithGameId($"{settings.GameId}-{number}");
        var own = new ThreadPlayer(name, create, botName, muted: false);
        var other = opponent.CreatePlayer();
        Player white = color == Color.White ? own : other;
        Player black = color == Color.White ? other : own;
        var outcome = new Match(white, black, settings).Play();
        if (own.Error is { } error)
        {
            ExceptionDispatchInfo.Throw(error);
        }
        return new PlayedGame(
            settings.GameId,
            color,
            opponent.Name,
            outcome.Result,
            outcome.Termination
        );
    }
}
