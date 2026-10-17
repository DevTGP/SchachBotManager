using System.IO.Pipes;
using System.Text;
using Sbm.Runtime.Play;
using Sbm.Runtime.Referee;

namespace Sbm.Tests.Runtime.Play;

/// <summary>Lines of a bot read in a background thread and awaited with a deadline.</summary>
public sealed class PlayerLinesTests : IDisposable
{
    private readonly AnonymousPipeServerStream _writer = new(PipeDirection.Out);
    private readonly AnonymousPipeClientStream _reader;
    private readonly PlayerLines _lines;

    public PlayerLinesTests()
    {
        _reader = new AnonymousPipeClientStream(PipeDirection.In, _writer.ClientSafePipeHandle);
        _lines = new PlayerLines(_reader, "bot");
    }

    public void Dispose()
    {
        _writer.Dispose();
        _reader.Dispose();
    }

    [Fact]
    public void LinesComeInOrderWithoutTheirEnd()
    {
        Write("one\ntwo\r\n");
        Assert.Equal("one", Receive(null));
        Assert.Equal("two", Receive(Later(5000)));
    }

    [Fact]
    public void NoLineBeforeTheDeadlineIsATimeout()
    {
        Assert.Throws<PlayerTimeoutException>(() => _lines.Receive(Later(50)));
        Assert.Throws<PlayerTimeoutException>(() => _lines.Receive(Monotonic.Now()));
    }

    [Fact]
    public void AWaitingLineIsReturnedAfterTheDeadline()
    {
        Write("late\n");
        Assert.Equal("late", Receive(Later(5000)));
        Write("waiting\n");
        Thread.Sleep(100);
        Assert.Equal("waiting", Receive(Monotonic.Now() - 1));
    }

    [Fact]
    public void TheEndOfTheStreamStays()
    {
        Write("last\n");
        _writer.Dispose();
        Assert.Equal("last", Receive(null));
        Assert.Throws<PlayerClosedException>(() => _lines.Receive(null));
        Assert.Throws<PlayerClosedException>(() => _lines.Receive(Later(5000)));
    }

    [Fact]
    public void ATooLongLineEndsTheReading()
    {
        Write(new string('x', Player.MaxLineBytes + 1) + "\nnext\n");
        Assert.Throws<LineTooLongException>(() => _lines.Receive(Later(5000)));
        Assert.Throws<LineTooLongException>(() => _lines.Receive(null));
    }

    private void Write(string text)
    {
        var bytes = Encoding.UTF8.GetBytes(text);
        _writer.Write(bytes);
        _writer.Flush();
    }

    private string Receive(long? deadlineNs) => Encoding.UTF8.GetString(_lines.Receive(deadlineNs));

    private static long Later(long ms) => Monotonic.Now() + ms * GameClock.NanosecondsPerMs;
}
