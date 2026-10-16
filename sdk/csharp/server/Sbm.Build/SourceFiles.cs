using System.Text;
using Microsoft.CodeAnalysis;
using Microsoft.CodeAnalysis.CSharp;
using Microsoft.CodeAnalysis.Text;

namespace Sbm.Build;

/// <summary>
/// The bot's sources: every .cs file outside data/, plus the files the server adds. The added
/// files have names no upload can have (verifikation.md), so they cannot be replaced.
/// </summary>
internal static class SourceFiles
{
    public const string GeneratedFolder = "<sbm>";

    // The implicit usings of a console project, as in the template (E201).
    private const string GlobalUsings = """
        global using System;
        global using System.Collections.Generic;
        global using System.IO;
        global using System.Linq;
        global using System.Net.Http;
        global using System.Threading;
        global using System.Threading.Tasks;
        """;

    private static readonly UTF8Encoding Utf8 = new(
        encoderShouldEmitUTF8Identifier: false,
        throwOnInvalidBytes: true
    );

    public static CSharpParseOptions ParseOptions { get; } =
        new(
            LanguageVersion.Latest,
            preprocessorSymbols:
            [
                "TRACE",
                "RELEASE",
                "NET",
                "NET10_0",
                "NET10_0_OR_GREATER",
                "NETCOREAPP",
            ]
        );

    /// <summary>The parsed sources of the bot; files that are no UTF-8 text become findings.</summary>
    public static List<SyntaxTree> Read(string botDir, List<Finding> findings)
    {
        var trees = new List<SyntaxTree>();
        var root = Path.GetFullPath(botDir);
        var paths = Directory
            .EnumerateFiles(root, "*.cs", SearchOption.AllDirectories)
            .Select(path => Path.GetRelativePath(root, path).Replace('\\', '/'))
            .Where(path => !path.StartsWith("data/", StringComparison.Ordinal))
            .Order(StringComparer.Ordinal);
        foreach (var path in paths)
        {
            var bytes = File.ReadAllBytes(Path.Combine(root, path));
            string text;
            try
            {
                text = Utf8.GetString(StripBom(bytes));
            }
            catch (DecoderFallbackException)
            {
                findings.Add(new Finding(Rules.Encoding, path, null, "not valid UTF-8"));
                continue;
            }
            trees.Add(Parse(text, path));
        }
        return trees;
    }

    /// <summary>The usings every bot project has implicitly.</summary>
    public static SyntaxTree Usings() => Parse(GlobalUsings, $"{GeneratedFolder}/GlobalUsings.cs");

    public static SyntaxTree Parse(string text, string path) =>
        CSharpSyntaxTree.ParseText(
            SourceText.From(text, Encoding.UTF8, SourceHashAlgorithm.Sha256),
            ParseOptions,
            path
        );

    private static ReadOnlySpan<byte> StripBom(byte[] bytes) =>
        bytes.AsSpan().StartsWith(Utf8.Preamble) ? bytes.AsSpan(Utf8.Preamble.Length) : bytes;
}
