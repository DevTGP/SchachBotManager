using System.Globalization;
using System.Text.Json.Nodes;

namespace Sbm.Tests;

/// <summary>Converts values between the encoding of the call vectors and C# (E55).</summary>
internal static class VectorCodec
{
    /// <summary>A vector argument as the value passed to a parameter of this C# type.</summary>
    public static object Decode(JsonNode? value, Type type)
    {
        ArgumentNullException.ThrowIfNull(value);
        if (type == typeof(Move))
        {
            return Move.FromValue(checked((ushort)value.GetValue<long>()));
        }
        if (type == typeof(string))
        {
            return value.GetValue<string>();
        }
        var number = value.GetValue<long>();
        if (type == typeof(byte))
        {
            return checked((byte)number);
        }
        if (type == typeof(ushort))
        {
            return checked((ushort)number);
        }
        if (type == typeof(int))
        {
            return checked((int)number);
        }
        throw new NotSupportedException("parameter type " + type);
    }

    /// <summary>A value returned by the binding in the encoding of the vectors.</summary>
    public static JsonNode? Encode(object? value, string typeName)
    {
        if (typeName.StartsWith("list<", StringComparison.Ordinal))
        {
            var item = typeName["list<".Length..^1];
            return new JsonArray(
                ((System.Collections.IEnumerable)value!)
                    .Cast<object>()
                    .Select(e => Encode(e, item))
                    .ToArray()
            );
        }
        return value switch
        {
            Move move => move.Value(),
            Board board => board.Fen(),
            PlacedPiece placed => new JsonObject
            {
                ["square"] = placed.Square,
                ["piece"] = placed.Piece,
            },
            ulong bits => "0x" + bits.ToString("x16", CultureInfo.InvariantCulture),
            bool flag => flag,
            byte small => small,
            ushort word => word,
            int number => number,
            string text => text,
            null => null,
            _ => throw new NotSupportedException("result type " + value.GetType()),
        };
    }
}
