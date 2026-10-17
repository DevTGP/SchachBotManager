using System.IO.Pipes;
using System.Runtime.InteropServices;
using System.Runtime.Versioning;

namespace Sbm.Runtime.Viewer;

/// <summary>
/// The viewer on Linux and macOS, started with posix_spawn in a session of its own: the arena
/// freezes the process group of the bot (E67), which must not freeze the window.
/// </summary>
[UnsupportedOSPlatform("windows")]
internal sealed unsafe partial class UnixViewerProcess : IViewerProcess
{
    private const string Libc = "libc";
    private const int Interrupted = 4; // EINTR
    private const int NoHang = 1; // WNOHANG
    private const int WriteOnly = 1; // O_WRONLY

    // POSIX_SPAWN_SETSID of macOS and glibc.
    private static readonly short NewSession = OperatingSystem.IsMacOS() ? (short)0x400 : (short)0x80;

    // Large enough for posix_spawnattr_t and posix_spawn_file_actions_t of glibc and macOS.
    private const int OpaqueSize = 1024;

    private readonly int _pid;
    private volatile bool _exited;

    private UnixViewerProcess(int pid, Stream input)
    {
        _pid = pid;
        Input = input;
    }

    public Stream Input { get; }

    public bool HasExited => _exited || Reap(NoHang);

    public void WaitForExit()
    {
        while (!_exited)
        {
            Reap(0);
        }
    }

    internal static UnixViewerProcess Start(string path)
    {
        // Both ends close on exec; posix_spawn hands the reading end over as stdin.
        var pipe = new AnonymousPipeServerStream(PipeDirection.Out, HandleInheritability.None);
        try
        {
            var pid = Spawn(path, (int)pipe.ClientSafePipeHandle.DangerousGetHandle());
            pipe.DisposeLocalCopyOfClientHandle();
            return new UnixViewerProcess(pid, pipe);
        }
        catch
        {
            pipe.Dispose();
            throw;
        }
    }

    /// <summary>True once the process has ended; a waitpid error also means it is gone.</summary>
    private bool Reap(int options)
    {
        int status;
        var result = waitpid(_pid, &status, options);
        if (result == _pid || (result == -1 && Marshal.GetLastPInvokeError() != Interrupted))
        {
            _exited = true;
        }
        return _exited;
    }

    private static int Spawn(string path, int stdin)
    {
        var strings = new List<nint>();
        var attributes = NativeMemory.AllocZeroed(OpaqueSize);
        var actions = NativeMemory.AllocZeroed(OpaqueSize);
        var attributesReady = false;
        var actionsReady = false;
        try
        {
            var program = Utf8(strings, path);
            var devNull = Utf8(strings, "/dev/null");
            nint[] arguments = [program, 0];
            var environment = Environment();
            nint[] variables = [.. environment.Select(variable => Utf8(strings, variable)), 0];
            Check(posix_spawnattr_init(attributes));
            attributesReady = true;
            Check(posix_spawnattr_setflags(attributes, NewSession));
            Check(posix_spawn_file_actions_init(actions));
            actionsReady = true;
            Check(posix_spawn_file_actions_adddup2(actions, stdin, 0));
            Check(posix_spawn_file_actions_addopen(actions, 1, devNull, WriteOnly, 0));
            int pid;
            fixed (nint* argv = arguments)
            fixed (nint* envp = variables)
            {
                Check(posix_spawn(&pid, program, actions, attributes, argv, envp));
            }
            return pid;
        }
        finally
        {
            if (actionsReady)
            {
                _ = posix_spawn_file_actions_destroy(actions);
            }
            if (attributesReady)
            {
                _ = posix_spawnattr_destroy(attributes);
            }
            NativeMemory.Free(actions);
            NativeMemory.Free(attributes);
            strings.ForEach(Marshal.FreeCoTaskMem);
        }
    }

    /// <summary>The environment as .NET sees it, which can differ from the one of the C library.</summary>
    private static List<string> Environment() =>
        [
            .. System
                .Environment.GetEnvironmentVariables()
                .Cast<System.Collections.DictionaryEntry>()
                .Select(entry => $"{entry.Key}={entry.Value}"),
        ];

    private static nint Utf8(List<nint> strings, string text)
    {
        var pointer = Marshal.StringToCoTaskMemUTF8(text);
        strings.Add(pointer);
        return pointer;
    }

    /// <summary>The posix_spawn functions return the error number instead of setting errno.</summary>
    private static void Check(int error)
    {
        if (error != 0)
        {
            throw new IOException(Marshal.GetPInvokeErrorMessage(error));
        }
    }

    [LibraryImport(Libc)]
    private static partial int posix_spawn(
        int* pid,
        nint path,
        void* fileActions,
        void* attributes,
        nint* argv,
        nint* envp
    );

    [LibraryImport(Libc)]
    private static partial int posix_spawnattr_init(void* attributes);

    [LibraryImport(Libc)]
    private static partial int posix_spawnattr_setflags(void* attributes, short flags);

    [LibraryImport(Libc)]
    private static partial int posix_spawnattr_destroy(void* attributes);

    [LibraryImport(Libc)]
    private static partial int posix_spawn_file_actions_init(void* actions);

    [LibraryImport(Libc)]
    private static partial int posix_spawn_file_actions_adddup2(void* actions, int from, int to);

    [LibraryImport(Libc)]
    private static partial int posix_spawn_file_actions_addopen(
        void* actions,
        int descriptor,
        nint path,
        int flags,
        uint mode
    );

    [LibraryImport(Libc)]
    private static partial int posix_spawn_file_actions_destroy(void* actions);

    [LibraryImport(Libc, SetLastError = true)]
    private static partial int waitpid(int pid, int* status, int options);
}
