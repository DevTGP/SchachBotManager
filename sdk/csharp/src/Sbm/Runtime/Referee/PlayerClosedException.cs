namespace Sbm.Runtime.Referee;

/// <summary>
/// The side is gone: the process ended or the connection closed. Termination is the code the
/// referee scores, crash unless the adapter knows better.
/// </summary>
internal sealed class PlayerClosedException : Exception
{
    public PlayerClosedException() { }

    public PlayerClosedException(string message)
        : base(message) { }

    public PlayerClosedException(string message, Exception innerException)
        : base(message, innerException) { }

    public PlayerClosedException(string message, string termination)
        : base(message) => Termination = termination;

    public string Termination { get; } = "crash";
}
