using System.Text;
using System.Text.Json;
using Sbm.Runtime;

namespace Sbm.Tests.Runtime;

/// <summary>Line channel: NDJSON framing, line limit and malformed input.</summary>
public class ChannelTests
{
    private static Channel Reading(byte[] data) => new(new MemoryStream(data), new MemoryStream());

    private static string Text(JsonElement? message) => message!.Value.GetRawText();

    [Fact]
    public void ReceivesLinesUntilEnd()
    {
        using var channel = Reading(
            "{\"type\":\"a\"}\n{\"type\":\"b\",\"x\":[1]}\r\n{\"type\":\"c\"}"u8.ToArray()
        );
        Assert.Equal("""{"type":"a"}""", Text(channel.Receive()));
        Assert.Equal("""{"type":"b","x":[1]}""", Text(channel.Receive()));
        Assert.Equal("""{"type":"c"}""", Text(channel.Receive()));
        Assert.Null(channel.Receive());
    }

    [Fact]
    public void LineLimit()
    {
        var text = new string('x', Channel.MaxLineBytes - """{"t":""}""".Length);
        var longest = Encoding.UTF8.GetBytes($$"""{"t":"{{text}}"}""");
        Assert.Equal(Channel.MaxLineBytes, longest.Length);
        var tooLong = Encoding.UTF8.GetBytes($$"""{"t":"{{text}}x"}""");
        using var channel = Reading([.. longest, (byte)'\r', (byte)'\n', .. tooLong, (byte)'\n']);
        Assert.Equal(text, channel.Receive()!.Value.GetProperty("t").GetString());
        var error = Assert.Throws<ProtocolException>(() => channel.Receive());
        Assert.Contains("longer", error.Message, StringComparison.Ordinal);
    }

    [Fact]
    public void EndlessLineStopsAtTheLimit()
    {
        using var channel = Reading([.. Enumerable.Repeat((byte)'x', 1_000_000)]);
        Assert.Throws<ProtocolException>(() => channel.Receive());
    }

    public static TheoryData<byte[]> MalformedLines() =>
        [
            "{"u8.ToArray(),
            "[1, 2]"u8.ToArray(),
            "\"text\""u8.ToArray(),
            new byte[] { 0xFF, 0xFE },
            "{} {}"u8.ToArray(),
            Array.Empty<byte>(),
        ];

    [Theory]
    [MemberData(nameof(MalformedLines))]
    public void MalformedLinesAreProtocolErrors(byte[] line)
    {
        using var channel = Reading([.. line, (byte)'\n']);
        Assert.Throws<ProtocolException>(() => channel.Receive());
    }

    [Fact]
    public void SendWritesOneCompactUtf8Line()
    {
        var output = new MemoryStream();
        using (var channel = new Channel(new MemoryStream(), output))
        {
            channel.Send(json =>
            {
                json.WriteStartObject();
                json.WriteString("type", "move");
                json.WriteNumber("v", 1);
                json.WriteStartObject("info");
                json.WriteString("text", "Läufer\nopfer ♗ <a&b>");
                json.WriteEndObject();
                json.WriteEndObject();
            });
            channel.Send(Protocol.Resign);
        }
        Assert.Equal(
            "{\"type\":\"move\",\"v\":1,\"info\":{\"text\":\"Läufer\\nopfer ♗ <a&b>\"}}\n"
                + "{\"type\":\"resign\",\"v\":1}\n",
            Encoding.UTF8.GetString(output.ToArray())
        );
    }
}
