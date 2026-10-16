namespace Sbm.Runtime;

/// <summary>The referee sent something the protocol does not allow; the SDK cannot continue.</summary>
internal sealed class ProtocolException : Exception
{
    public ProtocolException() { }

    public ProtocolException(string message)
        : base(message) { }

    public ProtocolException(string message, Exception innerException)
        : base(message, innerException) { }
}
