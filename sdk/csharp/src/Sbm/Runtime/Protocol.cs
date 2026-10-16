using System.Text.Json;

namespace Sbm.Runtime;

/// <summary>Messages of protocol version 1 (spec/protocol/v1/); unknown referee fields are ignored (E36).</summary>
internal static class Protocol
{
    internal const int Version = 1;
    internal const string Language = "csharp";

    /// <summary>The type of a message as it appears in errors, also if it is not a string.</summary>
    internal static string TypeOf(JsonElement message) =>
        message.TryGetProperty("type", out var type) && type.ValueKind == JsonValueKind.String
            ? type.GetString()!
            : Json(message, "type");

    /// <summary>A field as JSON text for the log, or None if it is missing.</summary>
    internal static string Json(JsonElement message, string name) =>
        message.TryGetProperty(name, out var value) ? value.GetRawText() : "None";

    internal static string String(JsonElement message, string name) =>
        Field(message, name, JsonValueKind.String, "a string").GetString()!;

    internal static long Integer(JsonElement message, string name) =>
        Field(message, name, JsonValueKind.Number, "an integer").TryGetInt64(out var value)
            ? value
            : throw Missing(message, name, "an integer");

    internal static int SmallInteger(JsonElement message, string name)
    {
        var value = Integer(message, name);
        return value is >= int.MinValue and <= int.MaxValue
            ? (int)value
            : throw Missing(message, name, "an integer");
    }

    /// <summary>The protocol versions in init.supported.</summary>
    internal static IReadOnlyList<JsonElement> Supported(JsonElement init) =>
        [.. Field(init, "supported", JsonValueKind.Array, "an array").EnumerateArray()];

    internal static bool IsThisVersion(JsonElement version) =>
        version.ValueKind == JsonValueKind.Number
        && version.TryGetInt64(out var number)
        && number == Version;

    internal static GameInfo GameInfo(JsonElement init)
    {
        var color = String(init, "color");
        var code = color switch
        {
            "white" => Color.White,
            "black" => Color.Black,
            _ => throw new ProtocolException($"init: unknown color {Native.Text.Quote(color)}"),
        };
        return new GameInfo(
            String(init, "game_id"),
            code,
            String(init, "opponent_name"),
            String(init, "start_fen"),
            Integer(init, "initial_time_ms"),
            Integer(init, "increment_ms"),
            Integer(init, "startup_ms"),
            SmallInteger(init, "memory_limit_mib"),
            String(init, "discipline")
        );
    }

    internal static GameResult GameResult(JsonElement gameOver) =>
        new(String(gameOver, "result"), String(gameOver, "termination"));

    internal static void Ready(Utf8JsonWriter json, string sdkVersion)
    {
        Start(json, "ready");
        json.WriteString("sdk", sdkVersion);
        json.WriteString("lang", Language);
        json.WriteEndObject();
    }

    internal static void Resign(Utf8JsonWriter json)
    {
        Start(json, "resign");
        json.WriteEndObject();
    }

    internal static void Move(Utf8JsonWriter json, string uci, Info? info)
    {
        Start(json, "move");
        json.WriteString("move", uci);
        if (info is not null)
        {
            json.WritePropertyName("info");
            InfoFields.Write(json, info);
        }
        json.WriteEndObject();
    }

    private static void Start(Utf8JsonWriter json, string type)
    {
        json.WriteStartObject();
        json.WriteString("type", type);
        json.WriteNumber("v", Version);
    }

    private static JsonElement Field(
        JsonElement message,
        string name,
        JsonValueKind kind,
        string what
    ) =>
        message.TryGetProperty(name, out var value) && value.ValueKind == kind
            ? value
            : throw Missing(message, name, what);

    private static ProtocolException Missing(JsonElement message, string name, string what) =>
        new($"{TypeOf(message)}: field '{name}' missing or not {what}");
}
