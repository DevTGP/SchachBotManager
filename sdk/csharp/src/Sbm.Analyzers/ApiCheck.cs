using Microsoft.CodeAnalysis;
using Microsoft.CodeAnalysis.CSharp.Syntax;
using Microsoft.CodeAnalysis.Diagnostics;

namespace Sbm.Analyzers;

/// <summary>
/// Every API a bot uses must be on the whitelist: each name is resolved to its symbol, and the
/// type of every expression is checked as well, so that no value of a forbidden type, e.g. from
/// typeof, passes unnoticed.
/// </summary>
internal sealed class ApiCheck
{
    private static readonly SymbolDisplayFormat Display = new(
        typeQualificationStyle: SymbolDisplayTypeQualificationStyle.NameAndContainingTypesAndNamespaces,
        memberOptions: SymbolDisplayMemberOptions.IncludeContainingType
    );

    private readonly SemanticModelAnalysisContext _context;
    private readonly RuleSet _rules;
    private readonly IAssemblySymbol _own;
    private readonly HashSet<(int Line, string Id, string Message)> _reported = [];

    private ApiCheck(SemanticModelAnalysisContext context, RuleSet rules)
    {
        _context = context;
        _rules = rules;
        _own = context.SemanticModel.Compilation.Assembly;
    }

    public static void Run(SemanticModelAnalysisContext context, RuleSet rules)
    {
        var check = new ApiCheck(context, rules);
        var model = context.SemanticModel;
        var token = context.CancellationToken;
        foreach (var node in model.SyntaxTree.GetRoot(token).DescendantNodes())
        {
            if (node is SimpleNameSyntax name)
            {
                var info = model.GetSymbolInfo(name, token);
                var symbol = info.Symbol ?? info.CandidateSymbols.FirstOrDefault();
                if (symbol is not null)
                {
                    check.Symbol(symbol, name);
                }
            }
            else if (node is ExpressionSyntax expression)
            {
                var info = model.GetTypeInfo(expression, token);
                check.Type(info.Type, expression);
                check.Type(info.ConvertedType, expression);
            }
        }
    }

    private void Symbol(ISymbol symbol, SyntaxNode node)
    {
        switch (symbol)
        {
            case IAliasSymbol alias:
                Symbol(alias.Target, node);
                break;
            case ITypeSymbol type:
                Type(type, node);
                break;
            case ILocalSymbol local:
                Type(local.Type, node);
                break;
            case IParameterSymbol parameter:
                Type(parameter.Type, node);
                break;
            case IMethodSymbol method:
                Method(method, node);
                break;
            case IPropertySymbol property:
                Member(property, node);
                Type(property.Type, node);
                break;
            case IFieldSymbol field:
                Member(field, node);
                Type(field.Type, node);
                break;
            case IEventSymbol @event:
                Member(@event, node);
                Type(@event.Type, node);
                break;
            default:
                // Namespaces, labels, range variables, discards: nothing to check.
                break;
        }
    }

    private void Method(IMethodSymbol method, SyntaxNode node)
    {
        if (method.MethodKind is MethodKind.LocalFunction or MethodKind.AnonymousFunction)
        {
            return;
        }
        Member(method.ReducedFrom ?? method, node);
        Type(method.ReturnType, node);
        foreach (var argument in method.TypeArguments)
        {
            Type(argument, node);
        }
    }

    private void Member(ISymbol member, SyntaxNode node)
    {
        var type = member.ContainingType;
        if (type is null || Own(type))
        {
            return;
        }
        Type(type, node);
        var outer = Outermost(type);
        if (_rules.ForbidsMember(FullName(outer), member.Name))
        {
            Report(Descriptors.ApiNotAllowed, node, member.ToDisplayString(Display));
        }
    }

    private void Type(ITypeSymbol? type, SyntaxNode node)
    {
        switch (type)
        {
            case null:
            case ITypeParameterSymbol:
                break;
            case IArrayTypeSymbol array:
                Type(array.ElementType, node);
                break;
            case IPointerTypeSymbol:
            case IFunctionPointerTypeSymbol:
                Report(Descriptors.Unsafe, node, "");
                break;
            case IDynamicTypeSymbol:
                Report(Descriptors.Dynamic, node, "dynamic");
                break;
            case INamedTypeSymbol named:
                Named(named, node);
                break;
            default:
                break;
        }
    }

    private void Named(INamedTypeSymbol type, SyntaxNode node)
    {
        if (
            type.TypeKind == TypeKind.Error
            || type.IsAnonymousType
            || type.SpecialType == SpecialType.System_Void
        )
        {
            return;
        }
        for (var current = type; current is not null; current = current.ContainingType)
        {
            foreach (var argument in current.TypeArguments)
            {
                Type(argument, node);
            }
        }
        if (Own(type))
        {
            return;
        }
        var outer = Outermost(type);
        if (!_rules.AllowsType(Namespace(outer), outer.Name))
        {
            Report(Descriptors.ApiNotAllowed, node, outer.ToDisplayString(Display));
        }
    }

    private bool Own(INamedTypeSymbol type) =>
        SymbolEqualityComparer.Default.Equals(type.ContainingAssembly, _own);

    private static INamedTypeSymbol Outermost(INamedTypeSymbol type)
    {
        var outer = type.OriginalDefinition;
        while (outer.ContainingType is not null)
        {
            outer = outer.ContainingType;
        }
        return outer;
    }

    private static string Namespace(INamedTypeSymbol type) =>
        type.ContainingNamespace is { IsGlobalNamespace: false } ns ? ns.ToDisplayString() : "";

    private static string FullName(INamedTypeSymbol type)
    {
        var ns = Namespace(type);
        return ns.Length == 0 ? type.Name : ns + "." + type.Name;
    }

    private void Report(DiagnosticDescriptor rule, SyntaxNode node, string argument)
    {
        var location = node.GetLocation();
        var line = location.GetLineSpan().StartLinePosition.Line;
        if (_reported.Add((line, rule.Id, argument)))
        {
            _context.ReportDiagnostic(Diagnostic.Create(rule, location, argument));
        }
    }
}
