using Sbm.Runtime.Referee;

namespace Sbm.Runtime.Play;

/// <summary>
/// Reads protocol lines from a bot in a background thread, so the referee can wait with a
/// deadline on pipes and sockets alike. The end of the stream and a too long line end the
/// reading; both stay, so every later call sees them too.
/// </summary>
internal sealed class PlayerLines
{
    private readonly Stream _stream;
    private readonly object _gate = new();
    private readonly Queue<byte[]> _lines = new();
    private Ending _ending;

    internal PlayerLines(Stream stream, string name)
    {
        _stream = stream;
        new Thread(Read) { Name = $"read {name}", IsBackground = true }.Start();
    }

    private enum Ending
    {
        None,
        Closed,
        TooLong,
    }

    /// <summary>
    /// The next line without its line end; throws PlayerTimeoutException, PlayerClosedException
    /// at the end or LineTooLongException. A waiting line is returned after the deadline too.
    /// </summary>
    internal byte[] Receive(long? deadlineNs)
    {
        lock (_gate)
        {
            while (true)
            {
                if (_lines.TryDequeue(out var line))
                {
                    return line;
                }
                switch (_ending)
                {
                    case Ending.Closed:
                        throw new PlayerClosedException("the bot closed its output");
                    case Ending.TooLong:
                        throw new LineTooLongException(
                            $"a line is longer than {Player.MaxLineBytes} bytes"
                        );
                }
                if (deadlineNs is not { } deadline)
                {
                    Monitor.Wait(_gate);
                    continue;
                }
                var leftNs = deadline - Monotonic.Now();
                if (leftNs <= 0)
                {
                    throw new PlayerTimeoutException();
                }
                // A tick is 100 ns; rounded up, so the wait does not end just before the deadline.
                Monitor.Wait(_gate, TimeSpan.FromTicks((leftNs + 99) / 100));
            }
        }
    }

    private void Read()
    {
        var reader = new LineReader(_stream);
        var ending = Ending.Closed;
        try
        {
            while (reader.ReadLine(Player.MaxLineBytes) is { } line)
            {
                lock (_gate)
                {
                    _lines.Enqueue(line);
                    Monitor.PulseAll(_gate);
                }
            }
        }
        catch (ProtocolException)
        {
            ending = Ending.TooLong;
        }
        // Closed while reading: the same as the end of the stream.
        catch (Exception error) when (error is IOException or ObjectDisposedException) { }
        lock (_gate)
        {
            _ending = ending;
            Monitor.PulseAll(_gate);
        }
    }
}
