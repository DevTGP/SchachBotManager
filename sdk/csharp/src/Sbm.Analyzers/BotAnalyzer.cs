using System.Collections.Immutable;
using Microsoft.CodeAnalysis;
using Microsoft.CodeAnalysis.Diagnostics;

namespace Sbm.Analyzers;

/// <summary>
/// The static analysis of C# bots (statische-analyse.md, E203): only whitelisted APIs and no
/// unsafe, external, asynchronous or dynamic code. Runs in the IDE and the build through the
/// NuGet package and on the server in the build tool; the sandbox stays the actual protection.
/// </summary>
[DiagnosticAnalyzer(LanguageNames.CSharp)]
public sealed class BotAnalyzer : DiagnosticAnalyzer
{
    private readonly RuleSet _rules;
    private readonly bool _generated;

    /// <summary>Uses the rules shipped with the assembly.</summary>
    public BotAnalyzer()
        : this(RuleSet.Default) { }

    /// <summary>Uses the given rules, e.g. in tests.</summary>
    /// <param name="rules">The whitelist.</param>
    /// <param name="generated">
    /// Also analyze code that looks generated (a name like *.g.cs or an auto-generated header).
    /// The server's build tool sets it, because an uploaded file could hide behind either; in
    /// the IDE the files the SDK generates, e.g. AssemblyInfo, stay out.
    /// </param>
    public BotAnalyzer(RuleSet rules, bool generated = false)
    {
        _rules = rules;
        _generated = generated;
    }

    /// <inheritdoc/>
    public override ImmutableArray<DiagnosticDescriptor> SupportedDiagnostics { get; } =
    [
        Descriptors.ApiNotAllowed,
        Descriptors.Unsafe,
        Descriptors.Extern,
        Descriptors.Async,
        Descriptors.Finalizer,
        Descriptors.Dynamic,
    ];

    /// <inheritdoc/>
    public override void Initialize(AnalysisContext context)
    {
        context.ConfigureGeneratedCodeAnalysis(
            _generated
                ? GeneratedCodeAnalysisFlags.Analyze | GeneratedCodeAnalysisFlags.ReportDiagnostics
                : GeneratedCodeAnalysisFlags.None
        );
        context.EnableConcurrentExecution();
        context.RegisterSyntaxTreeAction(SyntaxCheck.Run);
        context.RegisterSemanticModelAction(model => ApiCheck.Run(model, _rules));
    }
}
