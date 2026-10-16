namespace Sbm;

/// <summary>
/// The operation is not possible in the current state, e.g. undo without history or a null move
/// while in check.
/// </summary>
public sealed class InvalidStateException : ChessException
{
    /// <summary>An error without message.</summary>
    public InvalidStateException() { }

    /// <summary>An error with a message.</summary>
    public InvalidStateException(string message)
        : base(message) { }

    /// <summary>An error with a message and its cause.</summary>
    public InvalidStateException(string message, Exception innerException)
        : base(message, innerException) { }
}
