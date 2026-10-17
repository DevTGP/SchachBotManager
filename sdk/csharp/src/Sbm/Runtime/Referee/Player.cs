using System.Text.Json;

namespace Sbm.Runtime.Referee;

/// <summary>
/// One side of a game (match-runner.md, Spieler-Adapter): starts and stops the side and carries
/// protocol lines; the referee decides about everything else. Deadlines are values of
/// <see cref="Monotonic.Now"/>, null means no deadline. Exceptions other than
/// PlayerTimeoutException, PlayerClosedException and LineTooLongException are infrastructure
/// errors. Dispose ends the side after game_over, with a short grace period to exit on its own.
/// </summary>
internal abstract class Player(string name) : IDisposable
{
    internal const int MaxLineBytes = 65_536;

    internal string Name { get; } = name;

    /// <summary>Starts the side, e.g. launches its process; part of the startup budget.</summary>
    internal virtual void Start() { }

    /// <summary>Writes one message as one line; throws PlayerClosedException.</summary>
    internal abstract void Send(Action<Utf8JsonWriter> message);

    /// <summary>
    /// The next line without its line end. A line that is already waiting is returned even if
    /// the deadline has passed.
    /// </summary>
    internal abstract byte[] Receive(long? deadlineNs);

    /// <summary>Called after each own turn; the server freezes the process here.</summary>
    internal virtual void Suspend() { }

    /// <summary>Called before each own turn and before game_over.</summary>
    internal virtual void Resume() { }

    public void Dispose()
    {
        Dispose(true);
        GC.SuppressFinalize(this);
    }

    protected virtual void Dispose(bool disposing) { }
}
