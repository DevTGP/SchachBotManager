namespace Sbm.Analyzers.Tests;

public class AllowedTests
{
    private static string RepoFile(string path) =>
        File.ReadAllText(Path.Combine(AppContext.BaseDirectory, "../../../../../../..", path));

    [Fact]
    public void The_template_passes()
    {
        var findings = Analysis.Run(
            ("Program.cs", RepoFile("templates/csharp/Program.cs")),
            ("TemplateBot.cs", RepoFile("templates/csharp/TemplateBot.cs"))
        );

        Assert.Empty(findings);
    }

    [Fact]
    public void The_reference_bot_passes()
    {
        var findings = Analysis.Run(
            ("Program.cs", RepoFile("sdk/csharp/bots/Material/Program.cs")),
            ("MaterialBot.cs", RepoFile("sdk/csharp/bots/Material/MaterialBot.cs"))
        );

        Assert.Empty(findings);
    }

    [Theory]
    [InlineData("int M() => new List<int> { 1 }.Select(x => x * 2).Sum();")]
    [InlineData("long M() => System.Diagnostics.Stopwatch.GetTimestamp();")]
    [InlineData("int M() => System.Numerics.BitOperations.PopCount(5UL);")]
    [InlineData("string M() => new System.Text.StringBuilder().Append(1).ToString();")]
    [InlineData("string M() => $\"{1} {2.5:F1}\";")]
    [InlineData("int M() { Span<int> s = stackalloc int[4]; return s.Length; }")]
    [InlineData("(int, string) M() => (1, \"a\");")]
    [InlineData("int M() => new Lazy<int>(() => 1).Value + Random.Shared.Next();")]
    [InlineData("int M() => new PriorityQueue<int, int>().Count + Math.Max(1, 2);")]
    [InlineData("string M() => 1.5.ToString(System.Globalization.CultureInfo.InvariantCulture);")]
    [InlineData("int M() => \"a b\".AsSpan().IndexOf(' ');")]
    [InlineData("void M() => throw new InvalidOperationException(\"no\");")]
    [InlineData("int M() { try { return 1; } catch (Exception e) { return e.Message.Length; } }")]
    [InlineData("bool M(object o) => o.Equals(this) && GetHashCode() != 0;")]
    [InlineData("int M() => Enum.GetValues<StringComparison>().Length;")]
    [InlineData(
        "[System.Runtime.CompilerServices.MethodImpl(System.Runtime.CompilerServices.MethodImplOptions.AggressiveInlining)] int M() => 1;"
    )]
    [InlineData("IEnumerable<int> M() { yield return 1; }")]
    [InlineData("int M() { lock (this) { return 1; } }")]
    [InlineData("System.Numerics.BigInteger M() => System.Numerics.BigInteger.Pow(2, 100);")]
    [InlineData("byte[] M() => Sdk.LoadData(\"book.bin\");")]
    public void Allowed_code_passes(string members)
    {
        Assert.Empty(Analysis.Run(Analysis.Bot(members)));
    }

    [Fact]
    public void Own_types_pass_in_any_namespace()
    {
        var findings = Analysis.Run(
            ("Bot.cs", Analysis.Bot("int M() => System.IO.Helper.Twice(2);")),
            (
                "Helper.cs",
                "namespace System.IO { public static class Helper { public static int Twice(int x) => 2 * x; } }"
            )
        );

        Assert.Empty(findings);
    }
}
