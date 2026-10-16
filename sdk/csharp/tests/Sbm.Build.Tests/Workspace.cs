using Sbm.Analyzers;

namespace Sbm.Build.Tests;

/// <summary>A bot's folder and the reference folders, as the runner hands them to the tool.</summary>
internal sealed class Workspace : IDisposable
{
    private static readonly Lazy<string> SdkReferences = new(CopySdk);

    private readonly string _root = Directory.CreateTempSubdirectory("sbm-build-").FullName;

    public string Bot => _root;

    /// <summary>The ref pack of the running runtime plus a folder with only the SDK.</summary>
    public static IReadOnlyList<string> References => [RefPack(), SdkReferences.Value];

    public Workspace Add(string path, string source) => Add(path, Text.Encode(source));

    public Workspace Add(string path, byte[] bytes)
    {
        var full = Path.Combine(_root, path);
        Directory.CreateDirectory(Path.GetDirectoryName(full)!);
        File.WriteAllBytes(full, bytes);
        return this;
    }

    public BuildResult Build(string entry = "TestBot") => Build(entry, RuleSet.Default);

    public BuildResult Build(string entry, RuleSet rules) =>
        BotBuild.Run(new Options(entry, References, _root), rules);

    public void Dispose() => Directory.Delete(_root, recursive: true);

    /// <summary>The ref pack of the running runtime's major version, as on the server.</summary>
    private static string RefPack()
    {
        var shared = Path.GetDirectoryName(typeof(object).Assembly.Location)!;
        var root = Path.GetFullPath(Path.Combine(shared, "..", "..", ".."));
        var packs = Path.Combine(root, "packs", "Microsoft.NETCore.App.Ref");
        var major = Environment.Version.Major;
        var version = Directory
            .GetDirectories(packs, $"{major}.*")
            .Select(Path.GetFileName)
            .OrderBy(name => Version.Parse(name!))
            .Last();
        return Path.Combine(packs, version!, "ref", $"net{major}.0");
    }

    // The test's output folder holds many more assemblies than a bot may see.
    private static string CopySdk()
    {
        var folder = Directory.CreateTempSubdirectory("sbm-build-refs-").FullName;
        var sdk = typeof(Board).Assembly.Location;
        File.Copy(sdk, Path.Combine(folder, Path.GetFileName(sdk)));
        return folder;
    }
}

/// <summary>Sources of test bots.</summary>
internal static class Text
{
    public static byte[] Encode(string source) => System.Text.Encoding.UTF8.GetBytes(source);

    /// <summary>A bot class TestBot around the given members.</summary>
    public static string Bot(string members = "") =>
        $$"""
            using Sbm;

            public sealed class TestBot : Bot
            {
                public override Move ChooseMove(Board board, Clock clock) => board.LegalMoves()[0];
            {{members}}
            }
            """;
}
