using System.Reflection;

namespace Sbm.Tests;

/// <summary>Every Board and Move function of spec/api/ exists with its kind and parameter count.</summary>
public class ApiSurfaceTests
{
    private static readonly IReadOnlyDictionary<
        string,
        System.Text.Json.Nodes.JsonObject
    > Functions = SpecFiles.CoreFunctions();

    public static TheoryData<string> Names() => [.. Functions.Keys.Order(StringComparer.Ordinal)];

    [Theory]
    [MemberData(nameof(Names))]
    public void FunctionExists(string name)
    {
        var function = Functions[name];
        var owner = SpecFiles.Str(function, "owner") == "Board" ? typeof(Board) : typeof(Move);
        var count = function["params"]!.AsArray().Count;
        var kind = SpecFiles.Str(function, "kind");
        if (kind == "constructor")
        {
            Assert.Contains(owner.GetConstructors(), ctor => ctor.GetParameters().Length == count);
            return;
        }
        var flags =
            kind == "static"
                ? BindingFlags.Public | BindingFlags.Static
                : BindingFlags.Public | BindingFlags.Instance;
        var member = Tests.Names.Pascal(SpecFiles.Str(function, "name"));
        Assert.Contains(
            owner.GetMethods(flags),
            method => method.Name == member && method.GetParameters().Length == count
        );
    }
}
