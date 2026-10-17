using System.Text.Json.Nodes;

namespace Sbm.Tests.Runtime.Viewer;

/// <summary>The examples of spec/protocol/viewer-v1/.</summary>
internal static class ViewerFiles
{
    public static JsonObject Example(string name) =>
        JsonNode
            .Parse(
                File.ReadAllText(
                    Path.Combine(
                        SpecFiles.Spec,
                        "protocol",
                        "viewer-v1",
                        "examples",
                        "valid",
                        name + ".json"
                    )
                )
            )!
            .AsObject();

    public static readonly GameInfo BlackInfo = new(
        "66f1c2a9e4b0a1b2c3d4e5f6",
        Color.Black,
        "Random",
        new Board().Fen(),
        300000,
        2000,
        10000,
        1024,
        "Blitz"
    );

    public static string AfterE4 => Referee.Str(Example("move.own"), "fen");
}
