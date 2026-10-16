namespace Sbm.Tests;

/// <summary>Names of the specification in the spelling of C# (sdk-api.md).</summary>
internal static class Names
{
    /// <summary>snake_case or UPPER_CASE as PascalCase, e.g. make_move to MakeMove.</summary>
    public static string Pascal(string name) =>
        string.Concat(
            name.Split('_')
                .Select(part => char.ToUpperInvariant(part[0]) + part[1..].ToLowerInvariant())
        );
}
