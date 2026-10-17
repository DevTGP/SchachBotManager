using System.Text.Json.Nodes;

namespace Sbm.Runtime.Remote;

/// <summary>Opens a remote game: asks the web API for it and takes the seat (E116).</summary>
internal static class RemoteOpening
{
    /// <summary>The body of POST /remote/matches; a discipline wins over the time.</summary>
    internal static JsonObject RequestBody(RemoteOptions remote)
    {
        var body = new JsonObject { ["opponent"] = remote.Opponent, ["color"] = remote.Color };
        if (!string.IsNullOrEmpty(remote.Discipline))
        {
            body["discipline"] = remote.Discipline;
            return body;
        }
        long initialMs,
            incrementMs;
        try
        {
            (initialMs, incrementMs) = TimeControl.Parse(remote.Time);
        }
        catch (FormatException error)
        {
            throw new RemoteException(error.Message, "usage");
        }
        body["initial_time_ms"] = initialMs;
        body["increment_ms"] = incrementMs;
        return body;
    }

    /// <summary>Throws RemoteException if the server refuses the game or the seat.</summary>
    internal static (Seat Seat, RemoteChannel Channel) Open(RemoteOptions remote)
    {
        var body = RequestBody(remote);
        var seat = GameRequest.Request(remote.Url, remote.Token, body);
        Log.Info($"remote game {seat.MatchId} against {remote.Opponent}, playing {seat.Color}");
        return (seat, RemoteChannel.Join(seat));
    }
}
