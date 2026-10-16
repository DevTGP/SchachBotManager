using System.Reflection;
using System.Text.Json.Nodes;

namespace Sbm.Tests.Runtime;

/// <summary>Clock, Log, Bot, Run, LoadData and the records of spec/api/ exist with their parameters.</summary>
public sealed class RuntimeSurfaceTests
{
    // Sdk.Play and its record PlayedGame come with step 5 of M5 (E192).
    private static readonly IReadOnlyDictionary<string, JsonObject> Functions = SpecFiles
        .Functions("bot", "clock", "log", "runtime")
        .Where(function => SpecFiles.Str(function, "name") != "play")
        .ToDictionary(FullName);

    private static readonly IReadOnlyDictionary<string, JsonObject> Records = SpecFiles
        .Records()
        .Where(record => SpecFiles.Str(record, "name") != "PlayedGame")
        .ToDictionary(record => SpecFiles.Str(record, "name"));

    public static TheoryData<string> FunctionNames() =>
        [.. Functions.Keys.Order(StringComparer.Ordinal)];

    public static TheoryData<string> RecordNames() =>
        [.. Records.Keys.Order(StringComparer.Ordinal)];

    [Theory]
    [MemberData(nameof(FunctionNames))]
    public void FunctionExists(string name)
    {
        var function = Functions[name];
        var kind = SpecFiles.Str(function, "kind");
        var owner = kind == "free" ? typeof(Sdk) : OwnerType(SpecFiles.Str(function, "owner"));
        var flags = kind is "static" or "free"
            ? BindingFlags.Public | BindingFlags.Static
            : BindingFlags.Public | BindingFlags.Instance;
        var method = Assert.Single(
            owner.GetMethods(flags),
            method => method.Name == Names.Pascal(SpecFiles.Str(function, "name"))
        );
        Assert.Equal(kind == "callback", method.IsVirtual);
        // The bot of Sdk.Run is its type parameter.
        Assert.Equal(
            function["params"]!.AsArray().Count,
            method.GetGenericArguments().Length + method.GetParameters().Length
        );
    }

    [Fact]
    public void ChooseMoveIsTheOnlyRequiredCallback()
    {
        var methods = typeof(Bot).GetMethods(BindingFlags.Public | BindingFlags.Instance);
        Assert.Equal(["ChooseMove"], methods.Where(m => m.IsAbstract).Select(m => m.Name));
    }

    [Theory]
    [MemberData(nameof(RecordNames))]
    public void RecordFields(string name)
    {
        var type = typeof(Bot).Assembly.GetType("Sbm." + name)!;
        var properties = type.GetProperties(
            BindingFlags.Public | BindingFlags.Instance | BindingFlags.DeclaredOnly
        );
        Assert.Equal(
            Records[name]["fields"]!
                .AsArray()
                .Select(f => Names.Pascal(SpecFiles.Str(f!.AsObject(), "name"))),
            properties.Select(property => property.Name)
        );
    }

    private static string FullName(JsonObject function) =>
        function["owner"] is { } owner
            ? $"{owner.GetValue<string>()}.{SpecFiles.Str(function, "name")}"
            : SpecFiles.Str(function, "name");

    private static Type OwnerType(string owner) =>
        owner switch
        {
            "Bot" => typeof(Bot),
            "Clock" => typeof(Clock),
            "Log" => typeof(Log),
            _ => throw new ArgumentException(owner),
        };
}
