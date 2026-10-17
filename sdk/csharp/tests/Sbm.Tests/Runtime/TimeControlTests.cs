using Sbm.Runtime;

namespace Sbm.Tests.Runtime;

/// <summary>Time controls as SECONDS+INCREMENT, like sbm-arena --time.</summary>
public class TimeControlTests
{
    [Theory]
    [InlineData("60+1", 60_000, 1000)]
    [InlineData(" 30+0.5 ", 30_000, 500)]
    [InlineData("0.5", 500, 0)]
    [InlineData("0.001+0", 1, 0)]
    public void Valid(string text, long initialMs, long incrementMs) =>
        Assert.Equal((initialMs, incrementMs), TimeControl.Parse(text));

    [Theory]
    [InlineData("")]
    [InlineData("x")]
    [InlineData("60+")]
    [InlineData("+1")]
    [InlineData("1.2345")]
    [InlineData("-1")]
    [InlineData("1e3")]
    [InlineData("99999999999999999999999999999")]
    public void Invalid(string text)
    {
        var error = Assert.Throws<FormatException>(() => TimeControl.Parse(text));
        Assert.Equal(
            $"invalid time control '{text}', expected seconds+increment such as 60+1 or 0.5",
            error.Message
        );
    }

    [Fact]
    public void InitialTimeMustNotBeZero() =>
        Assert.Equal(
            "the initial time must be more than 0 seconds",
            Assert.Throws<FormatException>(() => TimeControl.Parse("0+1")).Message
        );
}
