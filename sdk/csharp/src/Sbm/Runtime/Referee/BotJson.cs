using System.Text;
using System.Text.Json;
using System.Text.Unicode;

namespace Sbm.Runtime.Referee;

/// <summary>
/// Reads one bot line as JSON the way Python's json module does, which the referee of the Python
/// SDK uses: duplicate keys keep the last value, escaped lone surrogates stay, numbers keep their
/// text. Objects become dictionaries, arrays lists, numbers NumberText.
/// </summary>
internal static class BotJson
{
    /// <summary>No bot message nests deeper than three levels.</summary>
    internal const int MaxDepth = 64;

    /// <summary>The value of the line; throws ViolationException.</summary>
    internal static object? Parse(byte[] line)
    {
        if (!Utf8.IsValid(line))
        {
            throw Invalid("the line is not valid UTF-8");
        }
        if (line.AsSpan().StartsWith("\xEF\xBB\xBF"u8))
        {
            throw Invalid("Unexpected UTF-8 BOM");
        }
        CheckSyntax(line);
        var reader = new Utf8JsonReader(line, Options());
        reader.Read();
        return Value(ref reader);
    }

    private static JsonReaderOptions Options() => new() { MaxDepth = 2 * MaxDepth };

    /// <summary>Reads all tokens once, so that the tree is only built from valid JSON.</summary>
    private static void CheckSyntax(byte[] line)
    {
        var reader = new Utf8JsonReader(line, Options());
        try
        {
            if (!reader.Read())
            {
                throw Invalid("Expecting value");
            }
            do
            {
                if (
                    reader.TokenType is JsonTokenType.StartObject or JsonTokenType.StartArray
                    && reader.CurrentDepth >= MaxDepth
                )
                {
                    throw new ViolationException(
                        "schema_violation",
                        "the message is nested too deeply"
                    );
                }
            } while (reader.Read());
        }
        catch (JsonException error)
        {
            throw Invalid(error.Message);
        }
    }

    private static ViolationException Invalid(string reason) =>
        new("invalid_json", $"invalid JSON: {reason}");

    private static object? Value(ref Utf8JsonReader reader) =>
        reader.TokenType switch
        {
            JsonTokenType.StartObject => Object(ref reader),
            JsonTokenType.StartArray => Array(ref reader),
            JsonTokenType.String => Text(ref reader),
            JsonTokenType.Number => new NumberText(Encoding.UTF8.GetString(reader.ValueSpan)),
            JsonTokenType.True => true,
            JsonTokenType.False => false,
            _ => null,
        };

    private static Dictionary<string, object?> Object(ref Utf8JsonReader reader)
    {
        var result = new Dictionary<string, object?>(StringComparer.Ordinal);
        while (reader.Read() && reader.TokenType == JsonTokenType.PropertyName)
        {
            var name = Text(ref reader);
            reader.Read();
            result[name] = Value(ref reader);
        }
        return result;
    }

    private static List<object?> Array(ref Utf8JsonReader reader)
    {
        var result = new List<object?>();
        while (reader.Read() && reader.TokenType != JsonTokenType.EndArray)
        {
            result.Add(Value(ref reader));
        }
        return result;
    }

    /// <summary>A string or property name; escapes are read here so that lone surrogates stay.</summary>
    private static string Text(ref Utf8JsonReader reader)
    {
        var raw = Encoding.UTF8.GetString(reader.ValueSpan);
        return reader.ValueIsEscaped ? Unescape(raw) : raw;
    }

    private static string Unescape(string raw)
    {
        var result = new StringBuilder(raw.Length);
        for (var index = 0; index < raw.Length; index++)
        {
            if (raw[index] != '\\')
            {
                result.Append(raw[index]);
                continue;
            }
            index++;
            switch (raw[index])
            {
                case 'b':
                    result.Append('\b');
                    break;
                case 'f':
                    result.Append('\f');
                    break;
                case 'n':
                    result.Append('\n');
                    break;
                case 'r':
                    result.Append('\r');
                    break;
                case 't':
                    result.Append('\t');
                    break;
                case 'u':
                    result.Append((char)Convert.ToUInt16(raw.Substring(index + 1, 4), 16));
                    index += 4;
                    break;
                default:
                    // " \ and /, the reader has rejected all other escapes.
                    result.Append(raw[index]);
                    break;
            }
        }
        return result.ToString();
    }
}
