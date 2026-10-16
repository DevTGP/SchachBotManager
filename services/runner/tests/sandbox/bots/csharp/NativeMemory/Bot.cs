// Fills 2 GiB outside the managed heap, twice its limit; exits with 42 if it is still alive
// (sandbox.md).
using Sbm;

Sdk.Run<SandboxSuite.NativeMemoryBot>();

namespace SandboxSuite
{
    public sealed unsafe class NativeMemoryBot : Bot
    {
        private const int Chunk = 64 << 20;
        private readonly List<nint> _chunks = [];

        public override Move ChooseMove(Board board, Clock clock)
        {
            for (var used = 0L; used < 2L << 30; used += Chunk)
            {
                var chunk = System.Runtime.InteropServices.NativeMemory.Alloc(Chunk);
                // Writing every byte makes the pages really used.
                new Span<byte>(chunk, Chunk).Fill(1);
                _chunks.Add((nint)chunk);
            }
            Environment.Exit(42);
            return Move.NullMove;
        }
    }
}
