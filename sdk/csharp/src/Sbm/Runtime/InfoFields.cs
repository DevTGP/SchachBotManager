using System.Globalization;
using System.Text;
using System.Text.Json;

namespace Sbm.Runtime;

/// <summary>
/// Info as the info object of a move message, within the limits of the protocol (E43, E63). A
/// field outside its limits would make the referee score a protocol violation, although info is
/// display only. The SDK therefore truncates pv and text and leaves out other invalid fields
/// with a warning.
/// </summary>
internal static class InfoFields
{
    internal const int MaxPvMoves = 32;
    internal const int MaxTextLength = 256;
    internal const long MaxNodes = (1L << 53) - 1;

    /// <summary>Writes the info object; empty if no field is set.</summary>
    internal static void Write(Utf8JsonWriter json, Info info)
    {
        var depth = Checked("depth", info.Depth, 0, 1024);
        var seldepth = Checked("seldepth", info.Seldepth, 0, 1024);
        var scoreCp = Checked("score_cp", info.ScoreCp, -100_000, 100_000);
        var scoreMate =
            info.ScoreMate == 0
                ? Rejected("score_mate", 0)
                : Checked("score_mate", info.ScoreMate, -1024, 1024);
        var nodes = Checked("nodes", info.Nodes, 0, MaxNodes);
        if (scoreCp is not null && scoreMate is not null)
        {
            Log.Warn("report: score_cp and score_mate are both set; only score_mate is sent");
            scoreCp = null;
        }
        json.WriteStartObject();
        WriteNumber(json, "depth", depth);
        WriteNumber(json, "seldepth", seldepth);
        WriteNumber(json, "score_cp", scoreCp);
        WriteNumber(json, "score_mate", scoreMate);
        WriteNumber(json, "nodes", nodes);
        if (info.Pv is not null)
        {
            json.WriteStartArray("pv");
            foreach (var uci in Pv(info.Pv))
            {
                json.WriteStringValue(uci);
            }
            json.WriteEndArray();
        }
        if (info.Text is not null)
        {
            json.WriteString("text", Text(info.Text));
        }
        json.WriteEndObject();
    }

    private static long? Checked(string name, long? value, long low, long high) =>
        value is null || (value >= low && value <= high) ? value : Rejected(name, value.Value);

    private static long? Rejected(string name, long value)
    {
        Log.Warn(
            string.Create(
                CultureInfo.InvariantCulture,
                $"report: {name}={value} is outside the protocol limits and is not sent"
            )
        );
        return null;
    }

    private static void WriteNumber(Utf8JsonWriter json, string name, long? value)
    {
        if (value is { } number)
        {
            json.WriteNumber(name, number);
        }
    }

    private static List<string> Pv(IReadOnlyList<Move> moves)
    {
        if (moves.Count > MaxPvMoves)
        {
            Log.Debug($"report: pv truncated to {MaxPvMoves} moves");
        }
        var pv = new List<string>();
        foreach (var move in moves.Take(MaxPvMoves))
        {
            try
            {
                pv.Add(move.Uci());
            }
            catch (ChessException)
            {
                Log.Warn($"report: pv ends before {move}, which has no UCI form");
                break;
            }
        }
        return pv;
    }

    /// <summary>At most 256 code points; lone surrogates, which have no UTF-8 form, become U+FFFD.</summary>
    private static string Text(string text)
    {
        var result = new StringBuilder();
        foreach (var rune in text.EnumerateRunes().Take(MaxTextLength))
        {
            result.Append(rune.ToString());
        }
        return result.ToString();
    }
}
