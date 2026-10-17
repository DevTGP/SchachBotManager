using System.Net;
using System.Net.Sockets;

namespace Sbm.Runtime.Play;

/// <summary>
/// A bot that plays in a thread of the calling program, for Sdk.Play (E120): the own bot, so a
/// debugger stops at its breakpoints, and the reference bots. The bot speaks the protocol over
/// a local socket pair, so the referee treats it like any other player. A thread cannot be
/// frozen: Suspend and Resume do nothing, as for a TCP bot. muted keeps the bot's log and its
/// game out of the log and the viewer window.
/// </summary>
internal sealed class ThreadPlayer(string name, Func<Bot> create, string botName, bool muted)
    : StreamPlayer(name)
{
    // The stack of the main thread on Linux and macOS; deep searches need more than the 1 MiB
    // that threads get by default.
    private const int StackBytes = 8 * 1024 * 1024;

    // Time the thread gets to end after game_over; a bot still thinking after a timeout keeps
    // running until ChooseMove returns, and its answer goes nowhere.
    private static readonly TimeSpan JoinTime = TimeSpan.FromSeconds(2);

    private Socket? _socket;
    private Thread? _thread;
    private volatile Exception? _error;

    /// <summary>What ended the bot's side early: a BotFailureException or a ProtocolException.</summary>
    internal Exception? Error => _error;

    internal override void Start()
    {
        var (own, other) = SocketPair();
        _socket = own;
        var stream = new NetworkStream(own, ownsSocket: false);
        Attach(stream, stream);
        _thread = new Thread(() => Play(other), StackBytes)
        {
            Name = $"bot {Name}",
            IsBackground = true,
        };
        _thread.Start();
    }

    protected override void Dispose(bool disposing)
    {
        if (disposing && _socket is not null)
        {
            // The end of the input lets the bot finish after game_over; then both sides close.
            Shutdown(SocketShutdown.Send);
            _thread!.Join(JoinTime);
            Shutdown(SocketShutdown.Both);
            _socket.Dispose();
        }
        base.Dispose(disposing);
    }

    private void Play(Socket connection)
    {
        Log.Muted = muted;
        var stream = new NetworkStream(connection, ownsSocket: true);
        using var channel = new Channel(stream, stream);
        try
        {
            new Game(Guard.Call($"{botName}()", create), channel).Play();
        }
        catch (Exception error) when (error is BotFailureException or ProtocolException)
        {
            _error = error;
        }
        catch (Exception error)
            when (error is IOException or SocketException or ObjectDisposedException)
        {
            // The referee closed the connection, e.g. after a timeout.
        }
    }

    private void Shutdown(SocketShutdown how)
    {
        try
        {
            _socket!.Shutdown(how);
        }
        catch (SocketException) { }
    }

    /// <summary>Two connected sockets on the loopback interface.</summary>
    private static (Socket Own, Socket Other) SocketPair()
    {
        using var listener = NewSocket();
        listener.Bind(new IPEndPoint(IPAddress.Loopback, 0));
        listener.Listen(1);
        var other = NewSocket();
        try
        {
            other.Connect(listener.LocalEndPoint!);
            while (true)
            {
                var own = listener.Accept();
                // Another program on this machine may have connected first.
                if (Equals(own.RemoteEndPoint, other.LocalEndPoint))
                {
                    own.NoDelay = true;
                    return (own, other);
                }
                own.Dispose();
            }
        }
        catch
        {
            other.Dispose();
            throw;
        }
    }

    private static Socket NewSocket() =>
        new(AddressFamily.InterNetwork, SocketType.Stream, ProtocolType.Tcp) { NoDelay = true };
}
