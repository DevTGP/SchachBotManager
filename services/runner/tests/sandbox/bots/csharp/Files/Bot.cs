// Tries to read and write outside its jail; exits with 42 if anything works (sandbox.md).
using System.Runtime.InteropServices;
using Sbm;

Sdk.Run<SandboxSuite.Files>();

namespace SandboxSuite
{
    public sealed partial class Files : Bot
    {
        private static readonly string[] Read =
        [
            "/etc/passwd",
            "/etc/shadow",
            "/proc/self/environ",
            "/opt/sbm/sandbox/csharp.cfg",
            "/sys/fs/cgroup/cgroup.procs",
            "/root/.bashrc",
        ];

        private static readonly string[] Write =
        [
            "/bot/written",
            "/program/written",
            "/tmp/written",
            "/written",
            "/usr/share/dotnet/written",
            "/dev/urandom",
        ];

        // The read-only root of the jail: .NET, its libraries, the loader, the launcher and the
        // mount points.
        private static readonly string[] Root =
        [
            "/bot",
            "/dev",
            "/etc",
            "/lib",
            "/lib64",
            "/program",
            "/sbm",
            "/usr",
        ];

        public override Move ChooseMove(Board board, Clock clock)
        {
            var breached =
                Read.Any(path => Opens(path, FileAccess.Read))
                || Write.Any(path => Opens(path, FileAccess.Write))
                || Directory.GetFileSystemEntries("/").Except(Root).Any()
                || GetUid() != 1000;
            if (breached)
            {
                Environment.Exit(42);
            }
            return board.LegalMoves()[0];
        }

        private static bool Opens(string path, FileAccess access)
        {
            try
            {
                using var file = new FileStream(path, FileMode.OpenOrCreate, access);
                if (access == FileAccess.Write)
                {
                    file.WriteByte(0x78);
                }
            }
            catch (Exception error) when (error is IOException or UnauthorizedAccessException)
            {
                return false;
            }
            return true;
        }

        [LibraryImport("libc", EntryPoint = "getuid")]
        private static partial uint GetUid();
    }
}
