// Starts threads until the process limit stops it; exits with 42 at 200 (sandbox.md).
using Sbm;

Sdk.Run<SandboxSuite.Threads>();

namespace SandboxSuite
{
    public sealed class Threads : Bot
    {
        private const int Enough = 200;

        public override void OnGameStart(GameInfo info)
        {
            using var stop = new ManualResetEventSlim();
            var started = new List<Thread>();
            try
            {
                while (started.Count < Enough)
                {
                    var thread = new Thread(() => stop.Wait(), 256 * 1024) { IsBackground = true };
                    thread.Start();
                    started.Add(thread);
                }
            }
            // .NET reports a refused thread as OutOfMemoryException or ThreadStartException.
            catch (SystemException) { }
            if (started.Count >= Enough)
            {
                Environment.Exit(42);
            }
            // .NET starts threads of its own while it runs, the console's on its first line, so
            // this bot gives its own back before it logs.
            stop.Set();
            started.ForEach(thread => thread.Join());
            Log.Info($"{started.Count} threads");
        }

        public override Move ChooseMove(Board board, Clock clock) => board.LegalMoves()[0];
    }
}
