namespace Sbm.Runtime.Referee;

/// <summary>A line breaks the protocol; Code is one of the error codes of error.schema.json.</summary>
internal sealed class ViolationException : Exception
{
    public ViolationException() { }

    public ViolationException(string message)
        : base(message) { }

    public ViolationException(string message, Exception innerException)
        : base(message, innerException) { }

    public ViolationException(string code, string message)
        : base(message) => Code = code;

    public string Code { get; } = "schema_violation";
}
