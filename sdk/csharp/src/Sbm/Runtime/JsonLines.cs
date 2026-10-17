using System.Buffers;
using System.Text.Encodings.Web;
using System.Text.Json;

namespace Sbm.Runtime;

/// <summary>One JSON message per line, as the referee and the viewer read it.</summary>
internal static class JsonLines
{
    private static readonly JsonWriterOptions WriterOptions = new()
    {
        Encoder = JavaScriptEncoder.UnsafeRelaxedJsonEscaping,
    };

    /// <summary>The message built by write, followed by a line feed.</summary>
    internal static ReadOnlyMemory<byte> Encode(Action<Utf8JsonWriter> write)
    {
        var buffer = new ArrayBufferWriter<byte>();
        using (var json = new Utf8JsonWriter(buffer, WriterOptions))
        {
            write(json);
        }
        buffer.Write("\n"u8);
        return buffer.WrittenMemory;
    }

    /// <summary>One received message, which must be a JSON object.</summary>
    internal static JsonElement Object(byte[] data)
    {
        JsonElement message;
        try
        {
            using var document = JsonDocument.Parse(data);
            message = document.RootElement.Clone();
        }
        catch (JsonException error)
        {
            throw new ProtocolException($"invalid JSON: {error.Message}");
        }
        if (message.ValueKind != JsonValueKind.Object)
        {
            var start = System.Text.Encoding.UTF8.GetString(data, 0, Math.Min(data.Length, 80));
            throw new ProtocolException($"message is not a JSON object: {start}");
        }
        return message;
    }

    /// <summary>The message built by write as text, without the line feed.</summary>
    internal static string Text(Action<Utf8JsonWriter> write)
    {
        var line = Encode(write);
        return System.Text.Encoding.UTF8.GetString(line.Span[..^1]);
    }
}
