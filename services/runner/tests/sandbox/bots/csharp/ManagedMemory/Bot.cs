// Fills 2 GiB on the managed heap; the heap limit of the jail ends the bot before the cgroup
// does, and it exits with 42 if it is still alive (sandbox.md).
using Sbm;

Sdk.Run<SandboxSuite.ManagedMemory>();

namespace SandboxSuite
{
    public sealed class ManagedMemory : Bot
    {
        private const int Chunk = 64 << 20;
        private readonly List<byte[]> _chunks = [];

        public override Move ChooseMove(Board board, Clock clock)
        {
            for (var used = 0L; used < 2L << 30; used += Chunk)
            {
                var chunk = new byte[Chunk];
                Array.Fill(chunk, (byte)1);
                _chunks.Add(chunk);
            }
            Environment.Exit(42);
            return Move.NullMove;
        }
    }
}
