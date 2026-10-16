namespace Sbm.Analyzers.Tests;

public class SyntaxTests
{
    [Theory]
    [InlineData("unsafe int M() => 1;", "SBM1002")]
    [InlineData("int M() { unsafe { return 1; } }", "SBM1002")]
    [InlineData("unsafe int M(int* p) => *p;", "SBM1002")]
    [InlineData("unsafe int M(int[] a) { fixed (int* p = a) { return *p; } }", "SBM1002")]
    [InlineData("unsafe delegate*<int> M() => null;", "SBM1002")]
    [InlineData("static extern int M();", "SBM1003")]
    [InlineData("async void M() { }", "SBM1004")]
    [InlineData(
        "async System.Threading.Tasks.Task M() => await System.Threading.Tasks.Task.Yield();",
        "SBM1004"
    )]
    [InlineData("~TestBot() { }", "SBM1005")]
    [InlineData("object M(dynamic d) => d.X;", "SBM1006")]
    [InlineData("int M(int x) { var r = __makeref(x); return __refvalue(r, int); }", "SBM1006")]
    public void Forbidden_features_are_reported(string members, string rule)
    {
        Assert.Contains(rule, Analysis.Rules(Analysis.Bot(members)));
    }

    [Fact]
    public void Contextual_keywords_as_names_pass()
    {
        var source = Analysis.Bot(
            "int M() { var async = 1; var await = 2; return async + await; }"
        );

        Assert.Empty(Analysis.Run(source));
    }
}
