using System.Text.Json;

namespace Sbm.Runtime;

/// <summary>The messages between the bot and the referee, over stdio, TCP or the gateway.</summary>
internal interface IChannel : IDisposable
{
    /// <summary>The next message, or null once the other side has closed the channel.</summary>
    JsonElement? Receive();

    /// <summary>Sends one message, built by write.</summary>
    void Send(Action<Utf8JsonWriter> write);
}
