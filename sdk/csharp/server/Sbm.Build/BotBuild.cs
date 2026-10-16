using System.Collections.Immutable;
using Microsoft.CodeAnalysis;
using Microsoft.CodeAnalysis.CSharp;
using Microsoft.CodeAnalysis.Diagnostics;
using Microsoft.CodeAnalysis.Emit;
using Sbm.Analyzers;
using RuleSet = Sbm.Analyzers.RuleSet;

namespace Sbm.Build;

/// <summary>The result: the build runs only after a clean analysis, the program only after both.</summary>
internal sealed record BuildResult(
    string Ruleset,
    Section Analysis,
    Section? Build,
    byte[]? Program
)
{
    public bool Ok => Analysis.Ok && Build is { Ok: true };
}

/// <summary>Analyzes and compiles a bot like a release build of the template (E201, E203).</summary>
internal static class BotBuild
{
    public const string AssemblyName = "Bot";

    public static BuildResult Run(Options options, RuleSet rules)
    {
        var findings = new List<Finding>();
        var sources = SourceFiles.Read(options.Bot, findings);
        findings.AddRange(EntryPoint.TopLevelStatements(sources));
        var entry = EntryPoint.Source(options.Entry);
        var compilation = CSharpCompilation.Create(
            AssemblyName,
            [.. sources, SourceFiles.Usings(), entry],
            References(options.References),
            CompilationOptions
        );
        findings.AddRange(Analyze(compilation, rules).Select(Diagnostics.From));
        var analysis = new Section(findings);
        if (!analysis.Ok)
        {
            return new BuildResult(rules.Name, analysis, null, null);
        }
        var problems = new List<Finding>();
        var program = Compile(compilation, options.Entry, entry, problems);
        if (program is not null)
        {
            problems.AddRange(ProgramCheck.Run(program, rules));
        }
        var build = new Section(problems);
        return new BuildResult(rules.Name, analysis, build, build.Ok ? program : null);
    }

    private static CSharpCompilationOptions CompilationOptions { get; } =
        new(
            OutputKind.ConsoleApplication,
            mainTypeName: EntryPoint.TypeName,
            optimizationLevel: OptimizationLevel.Release,
            allowUnsafe: false,
            deterministic: true,
            concurrentBuild: false,
            nullableContextOptions: NullableContextOptions.Enable
        );

    /// <summary>
    /// Read into memory: a reference from a file keeps it open, and the sandbox allows far fewer
    /// descriptors than there are reference assemblies.
    /// </summary>
    private static List<MetadataReference> References(IEnumerable<string> directories) =>
        directories
            .SelectMany(directory => Directory.GetFiles(directory, "*.dll"))
            .Order(StringComparer.Ordinal)
            .Select(path =>
                (MetadataReference)
                    MetadataReference.CreateFromImage(File.ReadAllBytes(path), filePath: path)
            )
            .ToList();

    /// <summary>
    /// Every finding of the analyzer, also those a #pragma or [SuppressMessage] would hide, and
    /// in files that look generated. A failing analyzer ends the tool with an exception.
    /// </summary>
    private static ImmutableArray<Diagnostic> Analyze(CSharpCompilation compilation, RuleSet rules)
    {
        var analyzers = ImmutableArray.Create<DiagnosticAnalyzer>(
            new BotAnalyzer(rules, generated: true)
        );
        var options = new CompilationWithAnalyzersOptions(
            new AnalyzerOptions([]),
            onAnalyzerException: (exception, _, _) =>
                throw new InvalidOperationException("the analyzer failed", exception),
            concurrentAnalysis: false,
            logAnalyzerExecutionTime: false,
            reportSuppressedDiagnostics: true
        );
        var diagnostics = compilation
            .WithAnalyzers(analyzers, options)
            .GetAnalyzerDiagnosticsAsync()
            .GetAwaiter()
            .GetResult();
        var failure = diagnostics.FirstOrDefault(diagnostic => diagnostic.Id == "AD0001");
        return failure is null
            ? diagnostics
            : throw new InvalidOperationException(failure.GetMessage());
    }

    /// <summary>The program, or null with the compiler's errors; warnings do not count.</summary>
    private static byte[]? Compile(
        CSharpCompilation compilation,
        string entryClass,
        SyntaxTree entry,
        List<Finding> problems
    )
    {
        var invalid = EntryPoint.CheckClass(compilation, entryClass);
        if (invalid is not null)
        {
            // The errors of the generated entry only repeat what the finding says.
            problems.Add(invalid);
        }
        using var stream = new MemoryStream();
        var result = compilation.Emit(
            stream,
            options: new EmitOptions(debugInformationFormat: DebugInformationFormat.Embedded)
        );
        problems.AddRange(
            result
                .Diagnostics.Where(diagnostic => diagnostic.Severity == DiagnosticSeverity.Error)
                .Where(diagnostic => invalid is null || diagnostic.Location.SourceTree != entry)
                .Select(Diagnostics.From)
        );
        return result.Success && invalid is null ? stream.ToArray() : null;
    }
}
