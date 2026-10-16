using System.Reflection;
using System.Reflection.Metadata;
using System.Reflection.Metadata.Ecma335;
using System.Reflection.PortableExecutable;
using Sbm.Analyzers;

namespace Sbm.Build;

/// <summary>
/// Checks the compiled program itself, independent of the analyzer: it may only reference the
/// whitelisted assemblies and contain no native code or calls into it (E203).
/// </summary>
internal static class ProgramCheck
{
    public const int MaxBytes = 4 * 1024 * 1024;

    public static List<Finding> Run(byte[] program, RuleSet rules)
    {
        var findings = new List<Finding>();
        if (program.Length > MaxBytes)
        {
            findings.Add(
                new Finding(
                    Rules.TooLarge,
                    "",
                    null,
                    $"the program has {program.Length} bytes, more than {MaxBytes}"
                )
            );
        }
        using var pe = new PEReader(new MemoryStream(program));
        var allowed = rules.Assemblies.ToHashSet(StringComparer.Ordinal);
        var metadata = pe.GetMetadataReader();
        foreach (var handle in metadata.AssemblyReferences)
        {
            var name = metadata.GetString(metadata.GetAssemblyReference(handle).Name);
            if (!allowed.Contains(name))
            {
                findings.Add(
                    new Finding(
                        Rules.Reference,
                        "",
                        null,
                        $"the reference to '{name}' is not allowed"
                    )
                );
            }
        }
        if (
            metadata.GetTableRowCount(TableIndex.ModuleRef) > 0
            || metadata.GetTableRowCount(TableIndex.ImplMap) > 0
            || metadata.MethodDefinitions.Any(handle =>
                Native(metadata.GetMethodDefinition(handle))
            )
            || pe.PEHeaders.CorHeader?.Flags.HasFlag(CorFlags.ILOnly) != true
        )
        {
            findings.Add(
                new Finding(Rules.NativeCode, "", null, "the program contains native code")
            );
        }
        return findings;
    }

    private static bool Native(MethodDefinition method) =>
        method.Attributes.HasFlag(MethodAttributes.PinvokeImpl)
        || method.ImplAttributes.HasFlag(MethodImplAttributes.InternalCall)
        || (method.ImplAttributes & MethodImplAttributes.CodeTypeMask) != MethodImplAttributes.IL
        || method.ImplAttributes.HasFlag(MethodImplAttributes.Unmanaged);
}
