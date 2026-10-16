namespace Sbm.Tests.Runtime;

/// <summary>Clock: the values of the turn and the elapsed time.</summary>
public sealed class ClockTests
{
    [Fact]
    public void Values()
    {
        var clock = new Clock(1500, 2500, 100);
        Assert.Equal(1500, clock.RemainingMs());
        Assert.Equal(2500, clock.OpponentRemainingMs());
        Assert.Equal(100, clock.IncrementMs());
        Assert.Equal(
            "Clock(remainingMs=1500, opponentRemainingMs=2500, incrementMs=100)",
            clock.ToString()
        );
    }

    [Fact]
    public void ElapsedTimeGrows()
    {
        var clock = new Clock(1500, 2500, 100);
        Assert.InRange(clock.ElapsedMs(), 0, 1000);
        Thread.Sleep(30);
        Assert.True(clock.ElapsedMs() >= 30);
        Assert.Equal(1500, clock.RemainingMs());
    }
}
