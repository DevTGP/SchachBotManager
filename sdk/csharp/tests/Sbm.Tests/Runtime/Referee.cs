using System.Text;
using System.Text.Json.Nodes;
using Sbm.Runtime;

namespace Sbm.Tests.Runtime;

/// <summary>A scripted referee: messages of spec/protocol/v1/ in, the bot's answers out.</summary>
internal static class Referee
{
    private static string Examples => Path.Combine(SpecFiles.Spec, "protocol", "v1", "examples");

    public static string StartFen => Str(Example("turn.first_move"), "fen");

    public static JsonObject Example(string name) =>
        Parse(File.ReadAllText(Path.Combine(Examples, "valid", name + ".json")));

    /// <summary>Names of the valid examples of one message type, e.g. init.standard.</summary>
    public static IEnumerable<string> ExampleNames(string type) =>
        Directory
            .EnumerateFiles(Path.Combine(Examples, "valid"), type + ".*.json")
            .Select(path => Path.GetFileNameWithoutExtension(path))
            .Order(StringComparer.Ordinal);

    public static JsonObject Turn(
        string fen,
        int ply,
        string? lastMove = null,
        long remainingMs = 1000
    ) =>
        new()
        {
            ["type"] = "turn",
            ["v"] = 1,
            ["last_move"] = lastMove,
            ["fen"] = fen,
            ["ply"] = ply,
            ["remaining_ms"] = remainingMs,
            ["opponent_remaining_ms"] = 2000,
        };

    /// <summary>A copy of the message with one field set, or removed for null.</summary>
    public static JsonObject With(JsonObject message, string name, JsonNode? value)
    {
        var copy = message.DeepClone().AsObject();
        copy[name] = value;
        return copy;
    }

    public static JsonObject Without(JsonObject message, string name)
    {
        var copy = message.DeepClone().AsObject();
        copy.Remove(name);
        return copy;
    }

    /// <summary>A channel that reads the messages and writes to the output.</summary>
    public static Channel Channel(IEnumerable<JsonObject> messages, MemoryStream output)
    {
        var data = string.Concat(messages.Select(message => message.ToJsonString() + "\n"));
        return new Channel(new MemoryStream(Encoding.UTF8.GetBytes(data)), output);
    }

    /// <summary>Plays the messages to the bot and returns its answers.</summary>
    public static List<JsonObject> Play(Bot bot, params JsonObject[] messages)
    {
        var output = new MemoryStream();
        new Game(bot, Channel(messages, output)).Play();
        return Answers(output);
    }

    public static List<JsonObject> Answers(MemoryStream output) =>
        [
            .. Encoding
                .UTF8.GetString(output.ToArray())
                .Split('\n', StringSplitOptions.RemoveEmptyEntries)
                .Select(Parse),
        ];

    public static string Str(JsonObject message, string name) => message[name]!.GetValue<string>();

    private static JsonObject Parse(string text) => JsonNode.Parse(text)!.AsObject();
}
