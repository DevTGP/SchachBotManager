namespace Sbm;

/// <summary>
/// A value is outside its range, e.g. a square above 63, a color above 1 or an unknown log
/// level.
/// </summary>
public sealed class InvalidArgumentException : ChessException
{
    /// <summary>An error without message.</summary>
    public InvalidArgumentException() { }

    /// <summary>An error with a message.</summary>
    public InvalidArgumentException(string message)
        : base(message) { }

    /// <summary>An error with a message and its cause.</summary>
    public InvalidArgumentException(string message, Exception innerException)
        : base(message, innerException) { }
}
