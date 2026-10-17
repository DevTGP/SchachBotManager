using System.Text.Json;

namespace Sbm.Runtime.Remote;

/// <summary>The remote game as a channel of referee messages, like stdio or TCP for Game (E116).</summary>
internal sealed class RemoteChannel : IChannel
{
    private static readonly TimeSpan JoinTimeout = TimeSpan.FromSeconds(45);

    private readonly RemoteSocket _socket;

    private RemoteChannel(RemoteSocket socket) => _socket = socket;

    /// <summary>Connects and takes the seat; throws RemoteException if the gateway refuses it.</summary>
    internal static RemoteChannel Join(Seat seat)
    {
        var socket = RemoteSocket.Connect(seat.SocketUrl);
        try
        {
            socket.Send(
                JsonLines
                    .Encode(json =>
                    {
                        json.WriteStartObject();
                        json.WriteString("type", "join");
                        json.WriteNumber("v", 1);
                        json.WriteString("match_id", seat.MatchId);
                        json.WriteString("seat", seat.Token);
                        json.WriteEndObject();
                    })
                    .Span[..^1]
            );
            byte[]? answer;
            try
            {
                answer = socket.Receive(JoinTimeout);
            }
            catch (TimeoutException)
            {
                throw new RemoteException("the game did not start in time", "no_game");
            }
            var message = answer is null ? (JsonElement?)null : JsonLines.Object(answer);
            if (message is not { } joined || Field(joined, "type") != "joined")
            {
                var code = message is { } refusal ? Field(refusal, "code") ?? "no_game" : "no_game";
                throw new RemoteException($"the server refused the seat ({code})", code);
            }
            return new RemoteChannel(socket);
        }
        catch
        {
            socket.Dispose();
            throw;
        }
    }

    public JsonElement? Receive()
    {
        var message = _socket.Receive();
        return message is null ? null : JsonLines.Object(message);
    }

    public void Send(Action<Utf8JsonWriter> write) =>
        _socket.Send(JsonLines.Encode(write).Span[..^1]);

    public void Dispose() => _socket.Dispose();

    private static string? Field(JsonElement message, string name) =>
        message.TryGetProperty(name, out var value) ? value.ToString() : null;
}
