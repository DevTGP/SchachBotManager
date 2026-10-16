namespace Sbm;

/// <summary>
/// Common base of all errors of the bot API (ChessError in spec/api/errors.json).
/// </summary>
public class ChessException : Exception
{
    /// <summary>An error without message.</summary>
    public ChessException() { }

    /// <summary>An error with a message.</summary>
    public ChessException(string message)
        : base(message) { }

    /// <summary>An error with a message and its cause.</summary>
    public ChessException(string message, Exception innerException)
        : base(message, innerException) { }
}
