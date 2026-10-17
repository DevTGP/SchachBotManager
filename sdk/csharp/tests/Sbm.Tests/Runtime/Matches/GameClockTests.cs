using Sbm.Runtime.Referee;

namespace Sbm.Tests.Runtime.Matches;

/// <summary>Wall-clock time of both sides with tolerance and increment (E19).</summary>
public sealed class GameClockTests
{
    private const long NsPerMs = GameClock.NanosecondsPerMs;

    [Fact]
    public void TurnsAreChargedWithTheIncrement()
    {
        var clock = new GameClock(new MatchSettings(1000, incrementMs: 100));
        clock.Charge(Color.White, 300);
        Assert.Equal(800, clock.RemainingMs(Color.White));
        Assert.Equal(1000, clock.RemainingMs(Color.Black));
    }

    [Fact]
    public void ToleranceFloorsAtZero()
    {
        var clock = new GameClock(new MatchSettings(1000, incrementMs: 100, toleranceMs: 20));
        Assert.False(clock.IsOver(Color.White, 1020));
        Assert.True(clock.IsOver(Color.White, 1021));
        clock.Charge(Color.White, 1020);
        Assert.Equal(100, clock.RemainingMs(Color.White));
    }

    [Fact]
    public void ATurnOverTheTimeCannotBeCharged()
    {
        var clock = new GameClock(new MatchSettings(1000, toleranceMs: 20));
        Assert.Throws<InvalidOperationException>(() => clock.Charge(Color.Black, 1021));
        clock.Flag(Color.Black);
        Assert.Equal(0, clock.RemainingMs(Color.Black));
    }

    [Fact]
    public void DeadlineCoversTheRemainingTimeAndTheTolerance()
    {
        var clock = new GameClock(new MatchSettings(1000, toleranceMs: 20));
        Assert.Equal(5 + 1020 * NsPerMs, clock.DeadlineNs(Color.White, 5));
    }

    [Fact]
    public void WithoutClockNothingCounts()
    {
        var clock = new GameClock(new MatchSettings(1000, incrementMs: 100, clock: false));
        Assert.False(clock.Running);
        Assert.Null(clock.DeadlineNs(Color.White, 0));
        Assert.False(clock.IsOver(Color.White, long.MaxValue / 2));
        clock.Charge(Color.White, 5000);
        Assert.Equal(1000, clock.RemainingMs(Color.White));
    }

    [Theory]
    [InlineData(0, 0, 0)]
    [InlineData(0, NsPerMs - 1, 0)]
    [InlineData(0, NsPerMs, 1)]
    [InlineData(NsPerMs, 0, -1)]
    [InlineData(1, 0, -1)]
    [InlineData(-5 * NsPerMs, 5 * NsPerMs + 1, 10)]
    public void ElapsedTimeIsRoundedDown(long startNs, long endNs, long elapsedMs) =>
        Assert.Equal(elapsedMs, GameClock.ElapsedMs(startNs, endNs));
}
