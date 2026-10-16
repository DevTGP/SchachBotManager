namespace Sbm.Tests.Runtime;

/// <summary>Log: line format, levels, ply and log file (E61).</summary>
[Collection(SharedLog.Name)]
public sealed class LogTests : IDisposable
{
    private readonly LogCapture _log = new();

    public void Dispose() => _log.Dispose();

    [Fact]
    public void LineFormat()
    {
        Log.Info("hello");
        Assert.Matches(@"^\d\d:\d\d:\d\d\.\d{3} \[ply -\] INFO  hello\n$", _log.Text);
    }

    [Fact]
    public void DefaultLevelIsInfo()
    {
        Assert.Equal(LogLevel.Info, Log.Level());
        Log.Trace("t");
        Log.Debug("d");
        Log.Info("i");
        Log.Warn("w");
        Log.Error("e");
        Assert.Equal(["INFO  i", "WARN  w", "ERROR e"], Lines());
    }

    [Fact]
    public void SetLevelAndIsEnabled()
    {
        Log.SetLevel(LogLevel.Trace);
        Assert.Equal(LogLevel.Trace, Log.Level());
        Assert.True(Log.IsEnabled(LogLevel.Trace));
        Log.Trace("t");
        Log.SetLevel(LogLevel.Warn);
        Assert.False(Log.IsEnabled(LogLevel.Info));
        Assert.True(Log.IsEnabled(LogLevel.Error));
        Log.Info("i");
        Log.SetLevel(LogLevel.Off);
        Assert.False(Log.IsEnabled(LogLevel.Error));
        Assert.False(Log.IsEnabled(LogLevel.Off));
        Log.Error("e");
        Assert.Equal(["TRACE t"], Lines());
    }

    [Theory]
    [InlineData(6)]
    [InlineData(255)]
    public void UnknownLevelsAreErrors(int value)
    {
        var level = (byte)value;
        var error = Assert.Throws<InvalidArgumentException>(() => Log.SetLevel(level));
        Assert.Equal($"Log.SetLevel: unknown level {level}", error.Message);
        error = Assert.Throws<InvalidArgumentException>(() => Log.IsEnabled(level));
        Assert.Equal($"Log.IsEnabled: unknown level {level}", error.Message);
        Assert.Equal(LogLevel.Info, Log.Level());
    }

    [Fact]
    public void PlyAndFile()
    {
        using var file = new StringWriter();
        Log.Configure(LogLevel.Debug, file);
        Log.SetPly(12);
        Log.Debug("deep");
        Assert.EndsWith(" [ply 12] DEBUG deep\n", _log.Text, StringComparison.Ordinal);
        Assert.Equal(_log.Text, file.ToString());
    }

    [Fact]
    public void LogIsAStaticClass() => Assert.True(typeof(Log).IsAbstract && typeof(Log).IsSealed);

    // The lines without time and ply.
    private string[] Lines() =>
        [
            .. _log
                .Text.Split('\n', StringSplitOptions.RemoveEmptyEntries)
                .Select(line => line[(line.IndexOf("] ", StringComparison.Ordinal) + 2)..]),
        ];
}
