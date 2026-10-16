namespace Sbm.Build.Tests;

public class OptionsTests
{
    [Fact]
    public void A_full_command_line_is_parsed()
    {
        var options = Options.Parse(
            ["--entry", "MyBot.TemplateBot", "--references", "/a", "--references", "/b", "/bot"],
            out var error
        );

        Assert.Equal("", error);
        Assert.Equal("MyBot.TemplateBot", options!.Entry);
        Assert.Equal(["/a", "/b"], options.References);
        Assert.Equal("/bot", options.Bot);
    }

    [Theory]
    [InlineData(new[] { "--entry", "Bot", "/bot" }, Options.Usage)]
    [InlineData(new[] { "--entry", "Bot", "--references", "/a" }, Options.Usage)]
    [InlineData(new[] { "--references", "/a", "/bot" }, Options.Usage)]
    [InlineData(new[] { "--entry" }, "--entry needs a value")]
    [InlineData(
        new[] { "--entry", "Bot", "--references", "/a", "/bot", "/other" },
        "unexpected argument '/other'"
    )]
    [InlineData(new[] { "--verbose" }, "unexpected argument '--verbose'")]
    [InlineData(
        new[] { "--entry", "Bot<int>", "--references", "/a", "/bot" },
        "'Bot<int>' is not a class name"
    )]
    [InlineData(
        new[] { "--entry", "global::Bot", "--references", "/a", "/bot" },
        "'global::Bot' is not a class name"
    )]
    [InlineData(
        new[] { "--entry", "A..B", "--references", "/a", "/bot" },
        "'A..B' is not a class name"
    )]
    public void A_wrong_command_line_is_refused(string[] args, string message)
    {
        Assert.Null(Options.Parse(args, out var error));
        Assert.Equal(message, error);
    }
}
