using Sbm.Runtime.Remote;

namespace Sbm.Runtime.Play;

/// <summary>One remote game of Sdk.Play (E120): open it, play it, report it.</summary>
internal static class RemoteGame
{
    // The server allows one running game per token; the previous one may still be ending.
    internal const string BusyCode = "too_many_games";
    internal const int BusyAttempts = 15;
    internal static readonly TimeSpan BusyWait = TimeSpan.FromSeconds(2);

    /// <summary>
    /// Throws RemoteException, BotFailureException or ProtocolException like the transport remote
    /// of Run. open and sleep are replaceable for tests.
    /// </summary>
    internal static PlayedGame Play(
        Func<Bot> create,
        string botName,
        RemoteOptions remote,
        Func<RemoteOptions, (Seat, IChannel)>? open = null,
        Action<TimeSpan>? sleep = null
    )
    {
        var (seat, channel) = OpenWhenFree(remote, open ?? Open, sleep ?? Thread.Sleep);
        Game game;
        using (channel)
        {
            game = new Game(Guard.Call($"{botName}()", create), channel);
            game.Play();
        }
        var (color, opponent) = game.Info is { } info
            ? (info.Color, info.OpponentName)
            : (seat.Color == "white" ? Color.White : Color.Black, remote.Opponent);
        // Without game_over the connection ended early; the site shows how the server scored it.
        var result = game.Result ?? new GameResult("*", "aborted");
        return new PlayedGame(seat.MatchId, color, opponent, result.Result, result.Termination);
    }

    /// <summary>Opens the game, waiting up to half a minute while the previous one ends.</summary>
    private static (Seat, IChannel) OpenWhenFree(
        RemoteOptions remote,
        Func<RemoteOptions, (Seat, IChannel)> open,
        Action<TimeSpan> sleep
    )
    {
        for (var attempt = 1; ; attempt++)
        {
            try
            {
                return open(remote);
            }
            catch (RemoteException error) when (error.Code == BusyCode && attempt < BusyAttempts)
            {
                sleep(BusyWait);
            }
        }
    }

    private static (Seat, IChannel) Open(RemoteOptions remote) => RemoteOpening.Open(remote);
}
