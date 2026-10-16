using Microsoft.CodeAnalysis;

namespace Sbm.Analyzers.Tests;

/// <summary>The reference assemblies a bot compiles against: the ref pack plus the SDK.</summary>
internal static class References
{
    public static IReadOnlyList<MetadataReference> All { get; } = Load();

    /// <summary>The ref pack of the running runtime's major version, as the server uses it.</summary>
    public static string RefPack()
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

    private static List<MetadataReference> Load()
    {
        var references = Directory
            .GetFiles(RefPack(), "*.dll")
            .Select(path => (MetadataReference)MetadataReference.CreateFromFile(path))
            .ToList();
        references.Add(MetadataReference.CreateFromFile(typeof(Board).Assembly.Location));
        return references;
    }
}
