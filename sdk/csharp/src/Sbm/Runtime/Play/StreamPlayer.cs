using System.Text.Json;
using Sbm.Runtime.Referee;

namespace Sbm.Runtime.Play;

/// <summary>
/// A player whose lines run over a pair of byte streams: a pipe or a socket. Subclasses connect
/// the streams with Attach in Start and remove them in Dispose.
/// </summary>
internal abstract class StreamPlayer(string name) : Player(name)
{
    private Stream? _writer;
    private PlayerLines? _lines;

    /// <summary>Set once game_over is sent: the bot may end on its own within a grace period.</summary>
    internal bool Finished { get; private set; }

    protected void Attach(Stream reader, Stream writer)
    {
        _lines = new PlayerLines(reader, Name);
        _writer = writer;
    }

    internal override void Send(Action<Utf8JsonWriter> message)
    {
        var line = JsonLines.Encode(message);
        try
        {
            _writer!.Write(line.Span);
            _writer.Flush();
        }
        catch (Exception error) when (error is IOException or ObjectDisposedException)
        {
            throw new PlayerClosedException($"cannot write to the bot: {error.Message}");
        }
        if (line.Span.StartsWith("{\"type\":\"game_over\""u8))
        {
            Finished = true;
        }
    }

    internal override byte[] Receive(long? deadlineNs)
    {
        try
        {
            return _lines!.Receive(deadlineNs);
        }
        catch (PlayerClosedException)
        {
            throw Closed();
        }
    }

    /// <summary>Why the bot's output ended, as precisely as the subclass knows.</summary>
    protected virtual PlayerClosedException Closed() => new("the bot closed its output");
}
