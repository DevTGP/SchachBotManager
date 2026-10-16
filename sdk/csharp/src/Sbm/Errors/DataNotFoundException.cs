namespace Sbm;

/// <summary>load_data found no data file with that name.</summary>
public sealed class DataNotFoundException : ChessException
{
    /// <summary>An error without message.</summary>
    public DataNotFoundException() { }

    /// <summary>An error with a message.</summary>
    public DataNotFoundException(string message)
        : base(message) { }

    /// <summary>An error with a message and its cause.</summary>
    public DataNotFoundException(string message, Exception innerException)
        : base(message, innerException) { }
}
