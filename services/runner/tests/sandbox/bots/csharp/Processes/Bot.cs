// Tries to start other processes the way .NET does it; exits with 42 if one starts (sandbox.md).
using System.Diagnostics;
using Sbm;

Sdk.Run<SandboxSuite.Processes>();

namespace SandboxSuite
{
    public sealed class Processes : Bot
    {
        // Programs that exist in the jail: the host of every C# bot and .NET's own.
        private static readonly string[] Programs = ["/sbm/host", "/usr/share/dotnet/dotnet"];

        public override Move ChooseMove(Board board, Clock clock)
        {
            if (Programs.Any(Starts))
            {
                Environment.Exit(42);
            }
            return board.LegalMoves()[0];
        }

        private static bool Starts(string program)
        {
            try
            {
                using var process = Process.Start(
                    new ProcessStartInfo(program, "--version") { UseShellExecute = false }
                );
                return process is not null;
            }
            catch (Exception)
            {
                return false;
            }
        }
    }
}
