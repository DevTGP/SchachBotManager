namespace Sbm.Runtime.Referee;

/// <summary>No line arrived before the deadline.</summary>
internal sealed class PlayerTimeoutException : Exception
{
    public PlayerTimeoutException() { }

    public PlayerTimeoutException(string message)
        : base(message) { }

    public PlayerTimeoutException(string message, Exception innerException)
        : base(message, innerException) { }
}
