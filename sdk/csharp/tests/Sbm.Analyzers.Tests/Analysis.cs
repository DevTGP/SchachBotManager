using System.Collections.Immutable;
using Microsoft.CodeAnalysis;
using Microsoft.CodeAnalysis.CSharp;
using Microsoft.CodeAnalysis.Diagnostics;

namespace Sbm.Analyzers.Tests;

/// <summary>A finding of the analyzer: rule, file, 1-based line and message.</summary>
internal sealed record Finding(string Rule, string File, int Line, string Message);

/// <summary>Compiles sources like a bot project and runs the analyzer over them.</summary>
internal static class Analysis
{
    // The implicit usings of a console project.
    private const string GlobalUsings = """
        global using System;
        global using System.Collections.Generic;
        global using System.IO;
        global using System.Linq;
        global using System.Net.Http;
        global using System.Threading;
        global using System.Threading.Tasks;
        """;

    private static readonly CSharpParseOptions ParseOptions = new(LanguageVersion.Latest);

    /// <summary>Findings for one file named Bot.cs.</summary>
    public static IReadOnlyList<Finding> Run(string source) => Run(("Bot.cs", source));

    /// <summary>Findings for several files; the sources must compile.</summary>
    public static IReadOnlyList<Finding> Run(params (string Path, string Source)[] files) =>
        Run(new BotAnalyzer(), files);

    /// <summary>Findings as the server's build tool gets them, generated code included.</summary>
    public static IReadOnlyList<Finding> RunAsServer(params (string Path, string Source)[] files) =>
        Run(new BotAnalyzer(RuleSet.Default, generated: true), files);

    private static List<Finding> Run(BotAnalyzer analyzer, (string Path, string Source)[] files)
    {
        var trees = files
            .Select(file => CSharpSyntaxTree.ParseText(file.Source, ParseOptions, file.Path))
            .Append(CSharpSyntaxTree.ParseText(GlobalUsings, ParseOptions, "GlobalUsings.g.cs"))
            .ToList();
        var options = new CSharpCompilationOptions(
            files.Any(file => file.Path == "Program.cs")
                ? OutputKind.ConsoleApplication
                : OutputKind.DynamicallyLinkedLibrary,
            nullableContextOptions: NullableContextOptions.Enable,
            allowUnsafe: true
        );
        var compilation = CSharpCompilation.Create("Bot", trees, References.All, options);
        var errors = compilation
            .GetDiagnostics()
            .Where(diagnostic => diagnostic.Severity == DiagnosticSeverity.Error)
            .ToList();
        Assert.True(errors.Count == 0, string.Join("\n", errors));
        var diagnostics = compilation
            .WithAnalyzers(ImmutableArray.Create<DiagnosticAnalyzer>(analyzer))
            .GetAnalyzerDiagnosticsAsync(TestContext.Current.CancellationToken)
            .GetAwaiter()
            .GetResult();
        return diagnostics
            .Select(diagnostic =>
            {
                var span = diagnostic.Location.GetLineSpan();
                return new Finding(
                    diagnostic.Id,
                    span.Path,
                    span.StartLinePosition.Line + 1,
                    diagnostic.GetMessage(System.Globalization.CultureInfo.InvariantCulture)
                );
            })
            .OrderBy(finding => finding.File, StringComparer.Ordinal)
            .ThenBy(finding => finding.Line)
            .ToList();
    }

    /// <summary>The rules found, without duplicates.</summary>
    public static IReadOnlyList<string> Rules(string source) =>
        Run(source).Select(finding => finding.Rule).Distinct().ToList();

    /// <summary>A bot class around the given members.</summary>
    public static string Bot(string members) =>
        $$"""
            using Sbm;

            public sealed class TestBot : Bot
            {
                public override Move ChooseMove(Board board, Clock clock) => board.LegalMoves()[0];

            {{members}}
            }
            """;
}
