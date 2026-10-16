namespace Sbm.Analyzers.Tests;

public class ApiTests
{
    [Theory]
    [InlineData("string M() => File.ReadAllText(\"x\");", "System.IO.File")]
    [InlineData("void M() => Console.WriteLine(1);", "System.Console")]
    [InlineData("void M() => Environment.Exit(1);", "System.Environment")]
    [InlineData("void M() => GC.Collect();", "System.GC")]
    [InlineData("object M() => typeof(int);", "System.Type")]
    [InlineData("object M() => GetType();", "System.Object.GetType")]
    [InlineData("object M() => Activator.CreateInstance<Board>();", "System.Activator")]
    [InlineData(
        "object M() => System.Reflection.Assembly.GetEntryAssembly()!;",
        "System.Reflection.Assembly"
    )]
    [InlineData(
        "void M() => System.Diagnostics.Process.Start(\"sh\");",
        "System.Diagnostics.Process"
    )]
    [InlineData("void M() => new Thread(() => { }).Start();", "System.Threading.Thread")]
    [InlineData("void M() => Task.Run(() => { });", "System.Threading.Tasks.Task")]
    [InlineData("object M() => new HttpClient();", "System.Net.Http.HttpClient")]
    [InlineData(
        "int M(Span<int> s) => System.Runtime.InteropServices.MemoryMarshal.GetReference(s);",
        "System.Runtime.InteropServices.MemoryMarshal"
    )]
    [InlineData(
        "int M(object o) => System.Runtime.CompilerServices.Unsafe.As<int[]>(o).Length;",
        "System.Runtime.CompilerServices.Unsafe"
    )]
    [InlineData(
        "[System.Runtime.InteropServices.DllImport(\"c\")] static extern int getpid();",
        "System.Runtime.InteropServices.DllImportAttribute"
    )]
    [InlineData("object M() => new[] { 1 }.AsQueryable();", "System.Linq.Queryable")]
    [InlineData("int M() => new[] { 1 }.AsParallel().Sum();", "System.Linq.ParallelEnumerable")]
    [InlineData(
        "object M() { System.Linq.Expressions.Expression<Func<int>> e = () => 1; return e; }",
        "System.Linq.Expressions.Expression"
    )]
    [InlineData("object M(Exception e) => e.TargetSite!;", "System.Exception.TargetSite")]
    [InlineData("object M(Func<int> f) => f.Method;", "System.Delegate")]
    [InlineData("object? M(Func<int> f) => f.DynamicInvoke();", "System.Delegate")]
    [InlineData("int M() => new List<Type>().Count;", "System.Type")]
    [InlineData("int M() => AppDomain.CurrentDomain.Id;", "System.AppDomain")]
    [InlineData(
        "string M() => System.Text.RegularExpressions.Regex.Escape(\"a\");",
        "System.Text.RegularExpressions.Regex"
    )]
    [InlineData(
        "int M() => Interlocked.Increment(ref _n);\nprivate int _n;",
        "System.Threading.Interlocked"
    )]
    public void Forbidden_api_is_reported(string members, string api)
    {
        var findings = Analysis.Run(Analysis.Bot(members));

        Assert.Contains(
            findings,
            finding => finding.Rule == "SBM1001" && finding.Message.Contains($"'{api}'")
        );
    }

    [Fact]
    public void A_forbidden_type_behind_an_alias_is_reported()
    {
        var findings = Analysis.Run(
            "using F = System.IO.File;\n\nclass C { string M() => F.ReadAllText(\"x\"); }"
        );

        Assert.Equal([1, 3], findings.Select(finding => finding.Line).Distinct());
        Assert.All(findings, finding => Assert.Equal("SBM1001", finding.Rule));
    }

    [Fact]
    public void A_finding_names_file_and_line()
    {
        var findings = Analysis.Run(
            ("Search/Deep.cs", "class C\n{\n    void M() => Console.Beep();\n}")
        );

        var finding = Assert.Single(findings);
        Assert.Equal(
            new Finding("SBM1001", "Search/Deep.cs", 3, "'System.Console' is not allowed in a bot"),
            finding
        );
    }

    [Fact]
    public void A_value_of_a_forbidden_type_is_reported_without_its_name()
    {
        var findings = Analysis.Run(Analysis.Bot("int M() => typeof(int).Name.Length;"));

        Assert.Contains(findings, finding => finding.Message.Contains("'System.Type'"));
    }
}
