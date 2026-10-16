namespace Sbm;

/// <summary>A well-formed move is not legal in the current position.</summary>
public sealed class IllegalMoveException : ChessException
{
    /// <summary>An error without message.</summary>
    public IllegalMoveException() { }

    /// <summary>An error with a message.</summary>
    public IllegalMoveException(string message)
        : base(message) { }

    /// <summary>An error with a message and its cause.</summary>
    public IllegalMoveException(string message, Exception innerException)
        : base(message, innerException) { }
}
