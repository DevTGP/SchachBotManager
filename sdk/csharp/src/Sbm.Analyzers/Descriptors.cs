using Microsoft.CodeAnalysis;

namespace Sbm.Analyzers;

/// <summary>The rules of the analyzer; their IDs appear in the verification report (E203).</summary>
internal static class Descriptors
{
    private const string Category = "SchachBotManager";

    public static readonly DiagnosticDescriptor ApiNotAllowed = Create(
        "SBM1001",
        "API not allowed",
        "'{0}' is not allowed in a bot"
    );

    public static readonly DiagnosticDescriptor Unsafe = Create(
        "SBM1002",
        "Unsafe code",
        "Unsafe code is not allowed in a bot"
    );

    public static readonly DiagnosticDescriptor Extern = Create(
        "SBM1003",
        "External code",
        "'extern' is not allowed in a bot"
    );

    public static readonly DiagnosticDescriptor Async = Create(
        "SBM1004",
        "Asynchronous code",
        "'{0}' is not allowed in a bot"
    );

    public static readonly DiagnosticDescriptor Finalizer = Create(
        "SBM1005",
        "Finalizer",
        "Finalizers are not allowed in a bot"
    );

    public static readonly DiagnosticDescriptor Dynamic = Create(
        "SBM1006",
        "Dynamic code",
        "'{0}' is not allowed in a bot"
    );

    private static DiagnosticDescriptor Create(string id, string title, string message) =>
        new(
            id,
            title,
            message,
            Category,
            DiagnosticSeverity.Error,
            isEnabledByDefault: true,
            helpLinkUri: "https://github.com/DevTGP/SchachBotManager/blob/master/docs/komponenten/statische-analyse.md"
        );
}
