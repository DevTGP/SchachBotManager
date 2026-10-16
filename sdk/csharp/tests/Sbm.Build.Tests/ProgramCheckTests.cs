using Microsoft.CodeAnalysis;
using Microsoft.CodeAnalysis.CSharp;
using RuleSet = Sbm.Analyzers.RuleSet;

namespace Sbm.Build.Tests;

/// <summary>The check of the compiled program, fed with assemblies the analyzer would refuse.</summary>
public class ProgramCheckTests
{
    [Fact]
    public void Native_code_is_reported()
    {
        var program = Compile(
            """
            public static class Native
            {
                [System.Runtime.InteropServices.DllImport("c")]
                public static extern int getpid();
            }
            """
        );

        var findings = ProgramCheck.Run(program, RuleSet.Default);

        Assert.Contains(
            new Finding("SBM2004", "", null, "the program contains native code"),
            findings
        );
    }

    [Fact]
    public void A_program_that_is_too_large_is_reported()
    {
        var program = Compile("public static class Empty { }");
        var padded = new byte[ProgramCheck.MaxBytes + 1];
        program.CopyTo(padded, 0);

        var finding = Assert.Single(ProgramCheck.Run(padded, RuleSet.Default));

        Assert.Equal("SBM2005", finding.Rule);
    }

    [Fact]
    public void A_plain_program_passes()
    {
        Assert.Empty(ProgramCheck.Run(Compile("public static class Empty { }"), RuleSet.Default));
    }

    private static byte[] Compile(string source)
    {
        var compilation = CSharpCompilation.Create(
            "Check",
            [CSharpSyntaxTree.ParseText(source)],
            Directory
                .GetFiles(Workspace.References[0], "*.dll")
                .Select(path => MetadataReference.CreateFromFile(path)),
            new CSharpCompilationOptions(OutputKind.DynamicallyLinkedLibrary)
        );
        using var stream = new MemoryStream();
        var result = compilation.Emit(stream);
        Assert.True(result.Success, string.Join("\n", result.Diagnostics));
        return stream.ToArray();
    }
}
