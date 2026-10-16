using System.Text.Json.Nodes;

namespace Sbm.Tests;

/// <summary>Reads the specification below spec/ that the tests compare the binding with.</summary>
internal static class SpecFiles
{
    // Modules of spec/api/ whose functions the core implements.
    private static readonly string[] CoreModules =
    [
        "board",
        "board_moves",
        "board_query",
        "board_raw",
        "board_state",
        "move",
    ];

    public static string Spec { get; } = FindSpec();

    /// <summary>Board and Move functions by their full name, e.g. Board.make_move.</summary>
    public static IReadOnlyDictionary<string, JsonObject> CoreFunctions() =>
        CoreModules
            .SelectMany(module =>
                Array(Load(Path.Combine(Spec, "api", module + ".json")), "functions")
            )
            .ToDictionary(function => $"{Str(function, "owner")}.{Str(function, "name")}");

    /// <summary>Call vectors (spec/testvectors/calls.schema.json) by their id.</summary>
    public static IReadOnlyDictionary<string, JsonObject> CallVectors() =>
        Directory
            .EnumerateFiles(
                Path.Combine(Spec, "testvectors"),
                "*.json",
                SearchOption.AllDirectories
            )
            .Where(path => !path.EndsWith(".schema.json", StringComparison.Ordinal))
            .Where(path => Path.GetFileName(path) != "perft.json")
            .Order(StringComparer.Ordinal)
            .SelectMany(path => Array(Load(path), "vectors"))
            .ToDictionary(vector => Str(vector, "id"));

    public static IEnumerable<JsonObject> Constants() =>
        Array(Load(Path.Combine(Spec, "api", "constants.json")), "constants");

    public static string Str(JsonObject node, string key) => node[key]!.GetValue<string>();

    private static IEnumerable<JsonObject> Array(JsonObject node, string key) =>
        node[key]!.AsArray().Select(entry => entry!.AsObject());

    private static JsonObject Load(string path) =>
        JsonNode.Parse(File.ReadAllText(path))!.AsObject();

    // The output directory lies below sdk/csharp; spec/ is in the root of the repository.
    private static string FindSpec()
    {
        for (var dir = new DirectoryInfo(AppContext.BaseDirectory); dir != null; dir = dir.Parent)
        {
            var spec = Path.Combine(dir.FullName, "spec");
            if (Directory.Exists(Path.Combine(spec, "api")))
            {
                return spec;
            }
        }
        throw new DirectoryNotFoundException(
            "spec/api not found above " + AppContext.BaseDirectory
        );
    }
}
