namespace Sbm;

/// <summary>A string is not a move in UCI notation.</summary>
public sealed class InvalidUciException : ChessException
{
    /// <summary>An error without message.</summary>
    public InvalidUciException() { }

    /// <summary>An error with a message.</summary>
    public InvalidUciException(string message)
        : base(message) { }

    /// <summary>An error with a message and its cause.</summary>
    public InvalidUciException(string message, Exception innerException)
        : base(message, innerException) { }
}
