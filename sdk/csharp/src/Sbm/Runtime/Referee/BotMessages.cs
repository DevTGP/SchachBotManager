using System.Numerics;
using System.Text.RegularExpressions;

namespace Sbm.Runtime.Referee;

/// <summary>
/// Strict reading of bot lines against spec/protocol/v1 (bot_message.schema.json, E66), with the
/// same verdicts and messages as the referee of the Python SDK.
/// </summary>
internal static partial class BotMessages
{
    internal const int Version = 1;

    private const int MaxSdkLength = 64;
    private const int MaxPvMoves = 32;
    private const int MaxTextLength = 256;
    private const int MaxNameLength = 64;
    private const int MaxUnknownNames = 8;

    private static readonly string[] Languages = ["cpp", "csharp", "java", "javascript", "python"];

    // Field and inclusive range from move.schema.json, in the order of the checks.
    private static readonly InfoInteger[] InfoIntegers =
    [
        new("depth", 0, 1024),
        new("seldepth", 0, 1024),
        new("score_cp", -100_000, 100_000),
        new("score_mate", -1024, 1024),
        new("nodes", 0, (1L << 53) - 1),
    ];

    /// <summary>The message in one line without its line end; throws ViolationException.</summary>
    internal static BotMessage Read(byte[] line)
    {
        if (BotJson.Parse(line) is not Dictionary<string, object?> message)
        {
            throw new ViolationException("schema_violation", "a message must be a JSON object");
        }
        if (!message.TryGetValue("type", out var type) || type is not string kind)
        {
            throw new ViolationException(
                "schema_violation",
                "field 'type' missing or not a string"
            );
        }
        switch (kind)
        {
            case "ready":
                return Ready(message);
            case "move":
                return Move(message);
            case "resign":
                Fields(message, kind, ["type", "v"], []);
                CheckVersion(message, kind);
                return new ResignMessage();
            default:
                throw new ViolationException(
                    "unknown_type",
                    $"a bot cannot send messages of type {PyText.Repr(PyText.Prefix(kind, 64))}"
                );
        }
    }

    /// <summary>The value as a JSON Schema integer: 3 and 3.0 count, true does not.</summary>
    internal static BigInteger? Integer(object? value) =>
        value is NumberText number ? number.Integer() : null;

    internal static bool IsUci(object? value) => value is string text && Uci().IsMatch(text);

    private static ReadyMessage Ready(Dictionary<string, object?> message)
    {
        Fields(message, "ready", ["type", "v", "sdk", "lang"], []);
        var version = Integer(message["v"]);
        if (version is { } number && number != Version)
        {
            throw new ViolationException(
                "unsupported_version",
                $"ready: version {number} is not one of the supported [{Version}]"
            );
        }
        CheckVersion(message, "ready");
        if (
            message["sdk"] is not string sdk
            || PyText.Length(sdk) > MaxSdkLength
            || !SdkVersion().IsMatch(sdk)
        )
        {
            throw Schema("ready", "sdk", "is not a SemVer version");
        }
        if (message["lang"] is not string lang || !Languages.Contains(lang))
        {
            throw Schema("ready", "lang", $"is not one of {PyText.Repr(Languages)}");
        }
        return new ReadyMessage(sdk, lang);
    }

    private static MoveMessage Move(Dictionary<string, object?> message)
    {
        Fields(message, "move", ["type", "v", "move"], ["info"]);
        CheckVersion(message, "move");
        if (message["move"] is not string uci || !IsUci(uci))
        {
            throw Schema("move", "move", "is not a move in UCI notation");
        }
        if (message.TryGetValue("info", out var info))
        {
            CheckInfo(info);
        }
        return new MoveMessage(uci);
    }

    private static void CheckInfo(object? value)
    {
        if (value is not Dictionary<string, object?> info)
        {
            throw Schema("move", "info", "is not an object");
        }
        var known = InfoIntegers.Select(field => field.Name).Concat(["pv", "text"]);
        var unknown = info.Keys.Except(known).Order(StringComparer.Ordinal).ToList();
        if (unknown.Count > 0)
        {
            throw Schema("move", "info", $"has unknown fields {PyText.Repr(unknown)}");
        }
        if (info.ContainsKey("score_cp") && info.ContainsKey("score_mate"))
        {
            throw Schema("move", "info", "has both score_cp and score_mate");
        }
        foreach (var field in InfoIntegers)
        {
            if (!info.TryGetValue(field.Name, out var number))
            {
                continue;
            }
            var integer = Integer(number);
            if (
                integer is not { } found
                || found < field.Low
                || found > field.High
                || (field.Name == "score_mate" && found.IsZero)
            )
            {
                throw Schema(
                    "move",
                    $"info.{field.Name}",
                    $"is not an integer in {field.Low}..{field.High}"
                );
            }
        }
        if (
            info.TryGetValue("pv", out var pv)
            && (pv is not List<object?> moves || moves.Count > MaxPvMoves || !moves.All(IsUci))
        )
        {
            throw Schema("move", "info.pv", $"is not a list of at most {MaxPvMoves} UCI moves");
        }
        if (
            info.TryGetValue("text", out var text)
            && (text is not string words || PyText.Length(words) > MaxTextLength)
        )
        {
            throw Schema("move", "info.text", $"is not a string of at most {MaxTextLength}");
        }
    }

    private static void Fields(
        Dictionary<string, object?> message,
        string kind,
        string[] required,
        string[] optional
    )
    {
        var missing = required.Where(name => !message.ContainsKey(name)).ToList();
        if (missing.Count > 0)
        {
            var names = missing.Order(StringComparer.Ordinal);
            throw new ViolationException(
                "schema_violation",
                $"{kind}: missing fields {PyText.Repr(names)}"
            );
        }
        var unknown = message.Keys.Except(required).Except(optional).ToList();
        if (unknown.Count > 0)
        {
            var names = unknown
                .Select(name => PyText.Prefix(name, MaxNameLength))
                .Order(StringComparer.Ordinal)
                .Take(MaxUnknownNames);
            throw new ViolationException(
                "schema_violation",
                $"{kind}: unknown fields {PyText.Repr(names)}"
            );
        }
    }

    private static void CheckVersion(Dictionary<string, object?> message, string kind)
    {
        if (Integer(message["v"]) != Version)
        {
            throw Schema(kind, "v", $"is not {Version}");
        }
    }

    private static ViolationException Schema(string kind, string field, string problem) =>
        new("schema_violation", $"{kind}: field {PyText.Repr(field)} {problem}");

    [GeneratedRegex(@"\A[a-h][1-8][a-h][1-8][nbrq]?\z")]
    private static partial Regex Uci();

    [GeneratedRegex(
        @"\A(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)(-[0-9A-Za-z.-]+)?(\+[0-9A-Za-z.-]+)?\z"
    )]
    private static partial Regex SdkVersion();

    private sealed record InfoInteger(string Name, long Low, long High);
}
