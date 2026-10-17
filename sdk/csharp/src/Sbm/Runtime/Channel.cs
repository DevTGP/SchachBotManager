using System.Text;
using System.Text.Json;

namespace Sbm.Runtime;

/// <summary>Line channel to the referee: one JSON message per line (NDJSON) over stdio or TCP.</summary>
internal sealed class Channel(Stream reader, Stream writer, IDisposable? closing = null)
    : IDisposable
{
    internal const int MaxLineBytes = 65_536;

    private readonly LineReader _lines = new(reader);

    /// <summary>The next message, or null at the end of the input.</summary>
    public JsonElement? Receive()
    {
        var line = _lines.ReadLine(MaxLineBytes);
        if (line is null)
        {
            return null;
        }
        JsonElement message;
        try
        {
            using var document = JsonDocument.Parse(line);
            message = document.RootElement.Clone();
        }
        catch (JsonException error)
        {
            throw new ProtocolException($"invalid JSON: {error.Message}");
        }
        if (message.ValueKind != JsonValueKind.Object)
        {
            var start = Encoding.UTF8.GetString(line, 0, Math.Min(line.Length, 80));
            throw new ProtocolException($"message is not a JSON object: {start}");
        }
        return message;
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
