using Microsoft.CodeAnalysis;
using Microsoft.CodeAnalysis.CSharp;
using Microsoft.CodeAnalysis.CSharp.Syntax;

namespace Sbm.Build;

/// <summary>
/// The server writes the program's entry itself (E203): Main calls Sdk.Run with the bot class
/// named at the upload; an uploaded file has no Program.cs and no top-level statements.
/// </summary>
internal static class EntryPoint
{
    public const string TypeName = "Sbm.Generated.Entry";

    /// <summary>The entry calling Sdk.Run with the given class.</summary>
    public static SyntaxTree Source(string entry) =>
        SourceFiles.Parse(
            $$"""
            namespace Sbm.Generated
            {
                internal static class Entry
                {
                    private static void Main() => global::Sbm.Sdk.Run<global::{{entry}}>();
                }
            }
            """,
            $"{SourceFiles.GeneratedFolder}/Entry.cs"
        );

    /// <summary>Top-level statements, which would be a second entry.</summary>
    public static IEnumerable<Finding> TopLevelStatements(IEnumerable<SyntaxTree> trees) =>
        trees
            .Select(tree =>
                tree.GetRoot().DescendantNodes().OfType<GlobalStatementSyntax>().FirstOrDefault()
            )
            .OfType<GlobalStatementSyntax>()
            .Select(statement =>
                Diagnostics.At(
                    Rules.TopLevelStatements,
                    statement.GetLocation(),
                    "top-level statements are not allowed; the server calls the bot class"
                )
            );

    /// <summary>What is wrong with the bot class, if anything.</summary>
    public static Finding? CheckClass(CSharpCompilation compilation, string entry)
    {
        var type = compilation.Assembly.GetTypeByMetadataName(entry);
        var bot = compilation.GetTypeByMetadataName("Sbm.Bot");
        string? problem = type switch
        {
            null => "is not a class of the bot",
            { TypeKind: not TypeKind.Class } => "is not a class",
            { IsAbstract: true } or { IsStatic: true } => "must not be abstract or static",
            _ when !Derives(type, bot) => "does not derive from Sbm.Bot",
            _ when !type.InstanceConstructors.Any(IsPublicDefault) =>
                "has no public constructor without parameters",
            _ when HasRequiredMembers(type) => "must not have required members",
            _ => null,
        };
        if (problem is null)
        {
            return null;
        }
        var location = type?.Locations.FirstOrDefault(location => location.IsInSource);
        var message = $"the bot class '{entry}' {problem}";
        return location is null
            ? new Finding(Rules.EntryClass, "", null, message)
            : Diagnostics.At(Rules.EntryClass, location, message);
    }

    private static bool Derives(INamedTypeSymbol type, INamedTypeSymbol? bot)
    {
        for (var current = type.BaseType; current is not null; current = current.BaseType)
        {
            if (SymbolEqualityComparer.Default.Equals(current, bot))
            {
                return true;
            }
        }
        return false;
    }

    private static bool HasRequiredMembers(INamedTypeSymbol type)
    {
        for (INamedTypeSymbol? current = type; current is not null; current = current.BaseType)
        {
            if (
                current
                    .GetMembers()
                    .Any(member =>
                        member
                            is IPropertySymbol { IsRequired: true }
                                or IFieldSymbol { IsRequired: true }
                    )
            )
            {
                return true;
            }
        }
        return false;
    }

    private static bool IsPublicDefault(IMethodSymbol constructor) =>
        constructor.Parameters.Length == 0
        && constructor.DeclaredAccessibility == Accessibility.Public;
}
