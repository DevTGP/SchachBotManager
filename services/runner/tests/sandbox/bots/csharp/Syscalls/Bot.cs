// Calls the kernel directly, past .NET; exits with 42 if a call the jail forbids works (sandbox.md).
using System.Runtime.InteropServices;
using Sbm;

Sdk.Run<SandboxSuite.Syscalls>();

namespace SandboxSuite
{
    public sealed partial class Syscalls : Bot
    {
        // x86-64 system call numbers and their arguments.
        private const long Socket = 41;
        private const long Ptrace = 101;
        private const long AfInet = 2;
        private const long SockStream = 1;
        private const long PtraceTraceMe = 0;

        public override Move ChooseMove(Board board, Clock clock)
        {
            var child = Fork();
            if (child == 0)
            {
                Exit(0);
            }
            var breached =
                child > 0
                || Syscall(Socket, AfInet, SockStream, 0) >= 0
                || Syscall(Ptrace, PtraceTraceMe, 0, 0) >= 0;
            if (breached)
            {
                Environment.Exit(42);
            }
            return board.LegalMoves()[0];
        }

        [LibraryImport("libc", EntryPoint = "fork")]
        private static partial int Fork();

        [LibraryImport("libc", EntryPoint = "_exit")]
        private static partial void Exit(int status);

        [LibraryImport("libc", EntryPoint = "syscall")]
        private static partial long Syscall(long number, long first, long second, long third);
    }
}
