namespace Sbm;

/// <summary>
/// A FEN string is malformed or describes an impossible position (e.g. no king, pawns on the
/// first or last rank, side not to move in check).
/// </summary>
public sealed class InvalidFenException : ChessException
{
    /// <summary>An error without message.</summary>
    public InvalidFenException() { }

    /// <summary>An error with a message.</summary>
    public InvalidFenException(string message)
        : base(message) { }

    /// <summary>An error with a message and its cause.</summary>
    public InvalidFenException(string message, Exception innerException)
        : base(message, innerException) { }
}
