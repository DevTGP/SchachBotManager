namespace Sbm.Runtime.Remote;

/// <summary>The web API or the gateway did not start the game; Code is the error code, e.g. too_many_games.</summary>
internal sealed class RemoteException : Exception
{
    internal const string Network = "network";

    public RemoteException() { }

    public RemoteException(string message)
        : base(message) { }

    public RemoteException(string message, Exception innerException)
        : base(message, innerException) { }

    public RemoteException(string message, string code)
        : base(message) => Code = code;

    public string Code { get; } = Network;
}
