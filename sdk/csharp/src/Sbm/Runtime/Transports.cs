using System.Net;
using System.Net.Sockets;

namespace Sbm.Runtime;

/// <summary>The channels to the referee (E197).</summary>
internal static class Transports
{
    /// <summary>
    /// Takes stdin and stdout for the protocol and points Console.Out to stderr and Console.In
    /// to an empty input, so that Console.WriteLine of the bot cannot corrupt the protocol
    /// stream. File descriptors 0 and 1 stay as they are.
    /// </summary>
    internal static Channel OpenStdio()
    {
        Console.Out.Flush();
        var reader = Console.OpenStandardInput();
        var writer = Console.OpenStandardOutput();
        Console.SetOut(Console.Error);
        Console.SetIn(TextReader.Null);
        return new Channel(reader, writer);
    }

    /// <summary>Connects to the waiting arena on this machine (local debugging only).</summary>
    internal static Channel OpenTcp(int port)
    {
        var client = new TcpClient { NoDelay = true };
        try
        {
            client.Connect(IPAddress.Loopback, port);
        }
        catch
        {
            client.Dispose();
            throw;
        }
        var stream = client.GetStream();
        return new Channel(stream, stream, client);
    }
}
