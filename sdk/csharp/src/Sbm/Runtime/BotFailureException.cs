namespace Sbm.Runtime;

/// <summary>A callback threw or returned something unusable; the process ends (E49).</summary>
internal sealed class BotFailureException : Exception
{
    public BotFailureException() { }

    public BotFailureException(string message)
        : base(message) { }

    public BotFailureException(string message, Exception innerException)
        : base(message, innerException) { }
}
