using System.Reflection;
using System.Text.Json.Nodes;

namespace Sbm.Tests;

/// <summary>Constants of the package against spec/api/constants.json.</summary>
public class ConstantsTests
{
    private static readonly Dictionary<string, JsonObject> Constants = SpecFiles
        .Constants()
        .ToDictionary(c => $"{SpecFiles.Str(c, "type")}.{SpecFiles.Str(c, "name")}");

    public static TheoryData<string> Keys() => [.. Constants.Keys];

    [Theory]
    [MemberData(nameof(Keys))]
    public void Constant(string key)
    {
        var constant = Constants[key];
        var type = SpecFiles.Str(constant, "type");
        var name = Names.Pascal(SpecFiles.Str(constant, "name"));
        var value = constant["value"]!.GetValue<long>();
        var field = typeof(Board).Assembly.GetType("Sbm." + type)!.GetField(name);
        Assert.NotNull(field);
        if (type == "Move")
        {
            Assert.Equal(Move.FromValue((ushort)value), field.GetValue(null));
        }
        else
        {
            Assert.True(field.IsLiteral);
            Assert.Equal((byte)value, Assert.IsType<byte>(field.GetValue(null)));
        }
    }

    [Theory]
    [InlineData(typeof(Color))]
    [InlineData(typeof(PieceType))]
    [InlineData(typeof(Piece))]
    [InlineData(typeof(Square))]
    [InlineData(typeof(CastlingRights))]
    [InlineData(typeof(MoveFlags))]
    [InlineData(typeof(LogLevel))]
    public void NoExtraConstants(Type owner)
    {
        var expected = Constants
            .Values.Where(c => SpecFiles.Str(c, "type") == owner.Name)
            .Select(c => Names.Pascal(SpecFiles.Str(c, "name")))
            .Order(StringComparer.Ordinal);
        var actual = owner
            .GetFields(BindingFlags.Public | BindingFlags.Static)
            .Select(field => field.Name)
            .Order(StringComparer.Ordinal);
        Assert.Equal(expected, actual);
    }
}
