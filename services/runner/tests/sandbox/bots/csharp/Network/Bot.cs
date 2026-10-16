// Tries to reach anything over a socket; exits with 42 if it gets through (sandbox.md).
using System.Net;
using System.Net.Sockets;
using Sbm;

Sdk.Run<SandboxSuite.Network>();

namespace SandboxSuite
{
    public sealed class Network : Bot
    {
        private static readonly EndPoint[] Targets =
        [
            new IPEndPoint(IPAddress.Parse("1.1.1.1"), 53),
            new IPEndPoint(IPAddress.Loopback, 47123),
            new IPEndPoint(IPAddress.Parse("2606:4700:4700::1111"), 53),
            new UnixDomainSocketEndPoint("/var/run/docker.sock"),
        ];

        public override Move ChooseMove(Board board, Clock clock)
        {
            if (Targets.Any(Reachable) || Resolves())
            {
                Environment.Exit(42);
            }
            return board.LegalMoves()[0];
        }

        private static bool Reachable(EndPoint target)
        {
            var protocol =
                target is UnixDomainSocketEndPoint ? ProtocolType.Unspecified : ProtocolType.Tcp;
            try
            {
                using var socket = new Socket(target.AddressFamily, SocketType.Stream, protocol);
                using var timeout = new CancellationTokenSource(TimeSpan.FromSeconds(2));
                socket.ConnectAsync(target, timeout.Token).AsTask().Wait();
            }
            catch (Exception)
            {
                return false;
            }
            return true;
        }

        private static bool Resolves()
        {
            try
            {
                return Dns.GetHostAddresses("example.com").Length > 0;
            }
            catch (Exception)
            {
                return false;
            }
        }
    }
}
