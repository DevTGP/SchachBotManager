namespace Sbm.Runtime.Play;

/// <summary>The opponent of Sdk.Play cannot be used as given.</summary>
internal sealed class OpponentException : Exception
{
    public OpponentException() { }

    public OpponentException(string message)
        : base(message) { }

    public OpponentException(string message, Exception innerException)
        : base(message, innerException) { }
}
