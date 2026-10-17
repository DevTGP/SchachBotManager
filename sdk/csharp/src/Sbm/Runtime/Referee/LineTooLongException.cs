namespace Sbm.Runtime.Referee;

/// <summary>The side wrote a line longer than <see cref="Player.MaxLineBytes"/>.</summary>
internal sealed class LineTooLongException : Exception
{
    public LineTooLongException() { }

    public LineTooLongException(string message)
        : base(message) { }

    public LineTooLongException(string message, Exception innerException)
        : base(message, innerException) { }
}
