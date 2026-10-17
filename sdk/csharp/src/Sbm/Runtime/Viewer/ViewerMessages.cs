using System.Text.Json;

namespace Sbm.Runtime.Viewer;

/// <summary>The messages the SDK writes to the viewer (spec/protocol/viewer-v1/).</summary>
internal static class ViewerMessages
{
    internal const int Version = 1;
    internal const int MaxNameLength = 64;
    internal const int MaxLogLength = 4096;

    private static readonly string[] LogLevels = ["debug", "debug", "info", "warn", "error"];

    internal static void Start(Utf8JsonWriter json, string bot, GameInfo info)
    {
        var name = CodePoints.Truncate(bot, MaxNameLength);
        json.WriteStartObject();
        json.WriteString("type", "start");
        json.WriteNumber("v", Version);
        json.WriteString("bot", name.Length > 0 ? name : "Bot");
        json.WriteString("color", info.Color == Color.White ? "white" : "black");
        json.WriteString("opponent", info.OpponentName);
        json.WriteString("start_fen", info.StartFen);
        json.WriteNumber("initial_time_ms", info.InitialTimeMs);
        json.WriteNumber("increment_ms", info.IncrementMs);
        if (info.Discipline.Length > 0)
        {
            json.WriteString("discipline", info.Discipline);
        }
        json.WriteEndObject();
    }

    /// <summary>
    /// clocks: remaining times of white and black after the move, if the SDK knows them; info:
    /// the info object of the move message as JSON text.
    /// </summary>
    internal static void Move(
        Utf8JsonWriter json,
        int ply,
        string uci,
        string fen,
        bool byBot,
        (long White, long Black)? clocks,
        long? elapsedMs = null,
        string? info = null
    )
    {
        json.WriteStartObject();
        json.WriteString("type", "move");
        json.WriteNumber("ply", ply);
        json.WriteString("move", uci);
        json.WriteString("fen", fen);
        json.WriteString("by", byBot ? "bot" : "opponent");
        if (clocks is var (white, black))
        {
            json.WriteNumber("white_ms", Math.Max(0, white));
            json.WriteNumber("black_ms", Math.Max(0, black));
        }
        if (elapsedMs is { } elapsed)
        {
            json.WriteNumber("elapsed_ms", Math.Max(0, elapsed));
        }
        if (info is not null && info != "{}")
        {
            json.WritePropertyName("info");
            json.WriteRawValue(info, skipInputValidation: true);
        }
        json.WriteEndObject();
    }

    internal static void Log(Utf8JsonWriter json, byte level, string time, string text)
    {
        json.WriteStartObject();
        json.WriteString("type", "log");
        json.WriteString("level", LogLevels[level]);
        json.WriteString("text", CodePoints.Truncate(text, MaxLogLength));
        json.WriteString("time", time);
        json.WriteEndObject();
    }
}
