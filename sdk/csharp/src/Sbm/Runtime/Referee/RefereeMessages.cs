using System.Text.Json;

namespace Sbm.Runtime.Referee;

/// <summary>Messages from the referee to a bot (spec/protocol/v1): init, turn, error, game_over.</summary>
internal static class RefereeMessages
{
    internal static readonly string[] ColorNames = ["white", "black"];

    private const int MaxErrorMessageLength = 1024;

    internal static Action<Utf8JsonWriter> Init(
        MatchSettings settings,
        byte color,
        string opponentName
    ) =>
        json =>
        {
            json.WriteStartObject();
            json.WriteString("type", "init");
            json.WriteStartArray("supported");
            json.WriteNumberValue(BotMessages.Version);
            json.WriteEndArray();
            json.WriteString("game_id", settings.GameId);
            json.WriteString("color", ColorNames[color]);
            json.WriteString("start_fen", settings.StartFen);
            json.WriteNumber("initial_time_ms", settings.InitialTimeMs);
            json.WriteNumber("increment_ms", settings.IncrementMs);
            json.WriteNumber("startup_ms", settings.StartupMs);
            json.WriteNumber("memory_limit_mib", settings.MemoryLimitMib);
            json.WriteString("discipline", settings.Discipline);
            json.WriteString("opponent_name", opponentName);
            json.WriteEndObject();
        };

    internal static Action<Utf8JsonWriter> Turn(
        string? lastMove,
        string fen,
        int ply,
        long remainingMs,
        long opponentRemainingMs
    ) =>
        json =>
        {
            json.WriteStartObject();
            json.WriteString("type", "turn");
            json.WriteNumber("v", BotMessages.Version);
            WriteMove(json, lastMove);
            json.WriteString("fen", fen);
            json.WriteNumber("ply", ply);
            json.WriteNumber("remaining_ms", remainingMs);
            json.WriteNumber("opponent_remaining_ms", opponentRemainingMs);
            json.WriteEndObject();
        };

    internal static Action<Utf8JsonWriter> Error(string code, string message) =>
        json =>
        {
            json.WriteStartObject();
            json.WriteString("type", "error");
            json.WriteString("code", code);
            json.WriteString("message", PyText.Prefix(message, MaxErrorMessageLength));
            json.WriteEndObject();
        };

    /// <summary>The final position lets the bot show the game to its end (E106).</summary>
    internal static Action<Utf8JsonWriter> GameOver(
        string result,
        string termination,
        string? lastMove,
        string fen,
        int ply
    ) =>
        json =>
        {
            json.WriteStartObject();
            json.WriteString("type", "game_over");
            json.WriteString("result", result);
            json.WriteString("termination", termination);
            WriteMove(json, lastMove);
            json.WriteString("fen", fen);
            json.WriteNumber("ply", ply);
            json.WriteEndObject();
        };

    private static void WriteMove(Utf8JsonWriter json, string? lastMove)
    {
        if (lastMove is null)
        {
            json.WriteNull("last_move");
        }
        else
        {
            json.WriteString("last_move", lastMove);
        }
    }
}
