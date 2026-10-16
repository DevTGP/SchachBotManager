using Microsoft.CodeAnalysis;
using Microsoft.CodeAnalysis.CSharp;
using Microsoft.CodeAnalysis.CSharp.Syntax;
using Microsoft.CodeAnalysis.Diagnostics;

namespace Sbm.Analyzers;

/// <summary>Language features a bot may not use, found in the syntax alone.</summary>
internal static class SyntaxCheck
{
    public static void Run(SyntaxTreeAnalysisContext context)
    {
        var root = context.Tree.GetRoot(context.CancellationToken);
        foreach (var token in root.DescendantTokens())
        {
            var rule = ForToken(token.Kind());
            if (rule is not null)
            {
                context.ReportDiagnostic(
                    Diagnostic.Create(rule, token.GetLocation(), token.ValueText)
                );
            }
        }
        foreach (var node in root.DescendantNodes())
        {
            var rule = ForNode(node);
            if (rule is not null)
            {
                context.ReportDiagnostic(Diagnostic.Create(rule, Location(node)));
            }
        }
    }

    private static DiagnosticDescriptor? ForToken(SyntaxKind kind) =>
        kind switch
        {
            SyntaxKind.UnsafeKeyword or SyntaxKind.FixedKeyword => Descriptors.Unsafe,
            SyntaxKind.ExternKeyword => Descriptors.Extern,
            SyntaxKind.AsyncKeyword or SyntaxKind.AwaitKeyword => Descriptors.Async,
            SyntaxKind.MakeRefKeyword
            or SyntaxKind.RefTypeKeyword
            or SyntaxKind.RefValueKeyword
            or SyntaxKind.ArgListKeyword => Descriptors.Dynamic,
            _ => null,
        };

    private static DiagnosticDescriptor? ForNode(SyntaxNode node) =>
        node switch
        {
            PointerTypeSyntax or FunctionPointerTypeSyntax => Descriptors.Unsafe,
            DestructorDeclarationSyntax => Descriptors.Finalizer,
            _ => null,
        };

    private static Location Location(SyntaxNode node) =>
        node is DestructorDeclarationSyntax destructor
            ? destructor.Identifier.GetLocation()
            : node.GetLocation();
}
