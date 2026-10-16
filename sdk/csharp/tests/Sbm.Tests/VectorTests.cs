using System.Reflection;
using System.Runtime.ExceptionServices;
using System.Text.Json.Nodes;

namespace Sbm.Tests;

/// <summary>Every Board and Move call vector of spec/testvectors/ against the binding (E55).</summary>
public class VectorTests
{
    private static readonly IReadOnlyDictionary<string, JsonObject> Functions =
        SpecFiles.CoreFunctions();
    private static readonly IReadOnlyDictionary<string, JsonObject> Vectors =
        SpecFiles.CallVectors();

    public static TheoryData<string> Ids() => [.. Vectors.Keys];

    [Fact]
    public void VectorsFound() => Assert.True(Vectors.Count > 500);

    [Theory]
    [MemberData(nameof(Ids))]
    public void CallVector(string id)
    {
        var vector = Vectors[id];
        var function = Functions[SpecFiles.Str(vector, "function")];
        var board = vector["board"] is JsonObject setup ? Setup(setup) : null;
        if (vector["error"] is JsonNode error)
        {
            var expected = typeof(Board).Assembly.GetType(
                $"Sbm.{error.GetValue<string>()}Exception"
            );
            Assert.NotNull(expected);
            Assert.IsType(
                expected,
                Assert.ThrowsAny<ChessException>(() => Call(vector, function, board))
            );
        }
        else
        {
            var result = Call(vector, function, board);
            var returns = function["returns"]?["type"]?.GetValue<string>();
            var actual = returns == null ? null : VectorCodec.Encode(result, returns);
            if (vector["result_contains"] is JsonNode part)
            {
                Assert.Contains(
                    part.GetValue<string>(),
                    actual!.GetValue<string>(),
                    StringComparison.Ordinal
                );
            }
            else if (vector["unordered"]?.GetValue<bool>() == true)
            {
                Assert.Equal(Sorted(vector["result"]), Sorted(actual));
            }
            else
            {
                Assert.True(
                    JsonNode.DeepEquals(vector["result"], actual),
                    $"expected {vector["result"]?.ToJsonString()}, got {actual?.ToJsonString()}"
                );
            }
        }
        if (vector["board_after"] is JsonNode after)
        {
            Assert.Equal(after.GetValue<string>(), board!.Fen());
        }
    }

    private static Board Setup(JsonObject setup)
    {
        var board = Board.FromFen(SpecFiles.Str(setup, "fen"));
        foreach (var uci in setup["moves"]!.AsArray().Select(move => move!.GetValue<string>()))
        {
            if (uci == "0000")
            {
                board.MakeNullMove();
            }
            else
            {
                board.MakeMove(board.ParseMove(uci));
            }
        }
        return board;
    }

    private static object? Call(JsonObject vector, JsonObject function, Board? board)
    {
        var owner = SpecFiles.Str(function, "owner") == "Board" ? typeof(Board) : typeof(Move);
        var kind = SpecFiles.Str(function, "kind");
        var args = vector["args"]!.AsArray();
        try
        {
            if (kind == "constructor")
            {
                var ctor = owner
                    .GetConstructors()
                    .Single(c => c.GetParameters().Length == args.Count);
                return ctor.Invoke(Decode(args, ctor));
            }
            var flags =
                kind == "static"
                    ? BindingFlags.Public | BindingFlags.Static
                    : BindingFlags.Public | BindingFlags.Instance;
            var name = Names.Pascal(SpecFiles.Str(function, "name"));
            var method = owner
                .GetMethods(flags)
                .Single(m => m.Name == name && m.GetParameters().Length == args.Count);
            object? target =
                kind == "static" ? null
                : owner == typeof(Board) ? board ?? new Board()
                : Move.FromValue(vector["move"]!.GetValue<ushort>());
            return method.Invoke(target, Decode(args, method));
        }
        catch (TargetInvocationException e) when (e.InnerException != null)
        {
            ExceptionDispatchInfo.Capture(e.InnerException).Throw();
            throw;
        }
    }

    private static object[] Decode(JsonArray args, MethodBase method) =>
        [
            .. method
                .GetParameters()
                .Select((param, i) => VectorCodec.Decode(args[i], param.ParameterType)),
        ];

    private static List<string> Sorted(JsonNode? list) =>
        [.. list!.AsArray().Select(entry => entry!.ToJsonString()).Order(StringComparer.Ordinal)];
}
