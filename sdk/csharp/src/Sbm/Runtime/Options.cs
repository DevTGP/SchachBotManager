namespace Sbm.Runtime;

internal enum Transport
{
    Stdio,
    Tcp,
    Remote,
}

/// <summary>Start options of Run from the command line and the environment (E61, E197).</summary>
internal sealed record Options
{
    internal const int DefaultPort = 7470;

    public Transport Transport { get; init; } = Transport.Stdio;

    public int Port { get; init; } = DefaultPort;

    public byte LogLevel { get; init; } = Sbm.LogLevel.Info;

    public string? LogFile { get; init; }

    /// <summary>Set for the transport remote only.</summary>
    public RemoteOptions? Remote { get; init; }
}

/// <summary>A game against a bot on the server (E116); Time is SECONDS+INCREMENT.</summary>
internal sealed record RemoteOptions(string Url, string Token, string Opponent)
{
    internal const string DefaultTime = "60+1";

    public string Color { get; init; } = "random";

    public string? Discipline { get; init; }

    public string Time { get; init; } = DefaultTime;
}

/// <summary>An argument or environment variable has an invalid value.</summary>
internal sealed class OptionsException : Exception
{
    public OptionsException() { }

    public OptionsException(string message)
        : base(message) { }

    public OptionsException(string message, Exception innerException)
        : base(message, innerException) { }
}
