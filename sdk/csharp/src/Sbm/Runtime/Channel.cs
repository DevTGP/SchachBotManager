using System.Text.Json;

namespace Sbm.Runtime;

/// <summary>Line channel to the referee: one JSON message per line (NDJSON) over stdio or TCP.</summary>
internal sealed class Channel(Stream reader, Stream writer, IDisposable? closing = null) : IChannel
{
    internal const int MaxLineBytes = 65_536;

    private readonly LineReader _lines = new(reader);

    /// <summary>The next message, or null at the end of the input.</summary>
    public JsonElement? Receive()
    {
        var line = _lines.ReadLine(MaxLineBytes);
        return line is null ? null : JsonLines.Object(line);
    }

    /// <summary>Writes one message, built by write, as a line and flushes it.</summary>
    public void Send(Action<Utf8JsonWriter> write)
    {
        writer.Write(JsonLines.Encode(write).Span);
        writer.Flush();
    }

    public void Dispose()
    {
        writer.Dispose();
        reader.Dispose();
        closing?.Dispose();
    }
}
