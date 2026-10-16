namespace Sbm.Analyzers.Tests;

public class RuleSetTests
{
    [Fact]
    public void The_shipped_rules_load()
    {
        var rules = RuleSet.Default;

        Assert.Equal("csharp-1", rules.Name);
        Assert.Contains("SchachBotManager", rules.Assemblies);
    }

    [Fact]
    public void A_namespace_allows_its_types_but_not_those_of_sub_namespaces()
    {
        var rules = RuleSet.Parse("ruleset t\nnamespace System.Linq\nforbid System.Linq.Queryable");

        Assert.True(rules.AllowsType("System.Linq", "Enumerable"));
        Assert.False(rules.AllowsType("System.Linq", "Queryable"));
        Assert.False(rules.AllowsType("System.Linq.Expressions", "Expression"));
        Assert.False(rules.AllowsType("System", "Console"));
    }

    [Fact]
    public void Single_types_and_members()
    {
        var rules = RuleSet.Parse(
            "# comment\n\nruleset t\ntype System.Math\nforbid System.Object.GetType\n"
        );

        Assert.True(rules.AllowsType("System", "Math"));
        Assert.False(rules.AllowsType("System", "MathF"));
        Assert.True(rules.ForbidsMember("System.Object", "GetType"));
        Assert.False(rules.ForbidsMember("System.Object", "Equals"));
    }

    [Theory]
    [InlineData("ruleset t\nallow System")]
    [InlineData("ruleset t\ntype")]
    [InlineData("ruleset t\ntype A B")]
    [InlineData("namespace System")]
    public void Invalid_rules_are_rejected(string text)
    {
        Assert.Throws<FormatException>(() => RuleSet.Parse(text));
    }
}
