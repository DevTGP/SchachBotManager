using System.ComponentModel;
using System.IO.Pipes;
using System.Runtime.InteropServices;
using System.Runtime.Versioning;
using Microsoft.Win32.SafeHandles;

namespace Sbm.Runtime.Viewer;

/// <summary>
/// The viewer on Windows, started outside the job object of the arena where the job allows it,
/// so that freezing the bot does not freeze the window; otherwise it starts inside.
/// </summary>
[SupportedOSPlatform("windows")]
internal sealed unsafe partial class WindowsViewerProcess(SafeProcessHandle process, Stream input)
    : IViewerProcess
{
    private const string Kernel = "kernel32.dll";
    private const uint BreakawayFromJob = 0x01000000; // CREATE_BREAKAWAY_FROM_JOB
    private const uint UseStdHandles = 0x100; // STARTF_USESTDHANDLES
    private const uint HandleFlagInherit = 1; // HANDLE_FLAG_INHERIT
    private const uint SameAccess = 2; // DUPLICATE_SAME_ACCESS
    private const int StdError = -12; // STD_ERROR_HANDLE
    private const int AccessDenied = 5; // ERROR_ACCESS_DENIED
    private const uint Infinite = 0xFFFFFFFF;

    public Stream Input { get; } = input;

    public bool HasExited => WaitForSingleObject(process, 0) == 0;

    public void WaitForExit() => WaitForSingleObject(process, Infinite);

    internal static WindowsViewerProcess Start(string path)
    {
        // The reading end is inherited as stdin, the writing end stays with the SDK.
        var pipe = new AnonymousPipeServerStream(PipeDirection.Out, HandleInheritability.Inheritable);
        try
        {
            using var output = File.OpenHandle("NUL", FileMode.Open, FileAccess.Write);
            Check(SetHandleInformation(output, HandleFlagInherit, HandleFlagInherit));
            using var error = InheritableStdError();
            var process = Create(path, pipe.ClientSafePipeHandle, output, error);
            pipe.DisposeLocalCopyOfClientHandle();
            return new WindowsViewerProcess(process, pipe);
        }
        catch
        {
            pipe.Dispose();
            throw;
        }
    }

    private static SafeProcessHandle Create(
        string path,
        SafeHandle input,
        SafeHandle output,
        SafeHandle? error
    )
    {
        var startup = new StartupInfo
        {
            Size = (uint)sizeof(StartupInfo),
            Flags = UseStdHandles,
            StdInput = input.DangerousGetHandle(),
            StdOutput = output.DangerousGetHandle(),
            StdError = error?.DangerousGetHandle() ?? 0,
        };
        // CreateProcessW may write into the command line.
        var commandLine = $"\"{path}\"\0".ToCharArray();
        ProcessInformation information;
        fixed (char* application = path)
        fixed (char* command = commandLine)
        {
            var created = CreateProcessW(
                application,
                command,
                0,
                0,
                true,
                BreakawayFromJob,
                0,
                null,
                &startup,
                &information
            );
            if (!created && Marshal.GetLastPInvokeError() == AccessDenied)
            {
                created = CreateProcessW(
                    application,
                    command,
                    0,
                    0,
                    true,
                    0,
                    0,
                    null,
                    &startup,
                    &information
                );
            }
            Check(created);
        }
        CloseHandle(information.Thread);
        return new SafeProcessHandle(information.Process, ownsHandle: true);
    }

    /// <summary>The viewer writes its own errors to the stderr of the bot program, if it has one.</summary>
    private static SafeFileHandle? InheritableStdError()
    {
        var current = GetCurrentProcess();
        var handle = GetStdHandle(StdError);
        if (handle is 0 or -1 || !DuplicateHandle(current, handle, current, out var copy, 0, true, SameAccess))
        {
            return null;
        }
        return new SafeFileHandle(copy, ownsHandle: true);
    }

    private static void Check(bool success)
    {
        if (!success)
        {
            throw new IOException(new Win32Exception(Marshal.GetLastPInvokeError()).Message);
        }
    }

    [StructLayout(LayoutKind.Sequential)]
    private struct StartupInfo
    {
        public uint Size;
        public nint Reserved;
        public nint Desktop;
        public nint Title;
        public uint X;
        public uint Y;
        public uint XSize;
        public uint YSize;
        public uint XCountChars;
        public uint YCountChars;
        public uint FillAttribute;
        public uint Flags;
        public ushort ShowWindow;
        public ushort Reserved2Size;
        public nint Reserved2;
        public nint StdInput;
        public nint StdOutput;
        public nint StdError;
    }

    [StructLayout(LayoutKind.Sequential)]
    private struct ProcessInformation
    {
        public nint Process;
        public nint Thread;
        public uint ProcessId;
        public uint ThreadId;
    }

    [LibraryImport(Kernel, SetLastError = true)]
    [return: MarshalAs(UnmanagedType.Bool)]
    private static partial bool CreateProcessW(
        char* application,
        char* commandLine,
        nint processAttributes,
        nint threadAttributes,
        [MarshalAs(UnmanagedType.Bool)] bool inheritHandles,
        uint creationFlags,
        nint environment,
        char* directory,
        StartupInfo* startup,
        ProcessInformation* information
    );

    [LibraryImport(Kernel, SetLastError = true)]
    [return: MarshalAs(UnmanagedType.Bool)]
    private static partial bool SetHandleInformation(SafeHandle handle, uint mask, uint flags);

    [LibraryImport(Kernel, SetLastError = true)]
    [return: MarshalAs(UnmanagedType.Bool)]
    private static partial bool DuplicateHandle(
        nint sourceProcess,
        nint source,
        nint targetProcess,
        out nint target,
        uint access,
        [MarshalAs(UnmanagedType.Bool)] bool inherit,
        uint options
    );

    [LibraryImport(Kernel)]
    private static partial nint GetStdHandle(int which);

    [LibraryImport(Kernel)]
    private static partial nint GetCurrentProcess();

    [LibraryImport(Kernel)]
    [return: MarshalAs(UnmanagedType.Bool)]
    private static partial bool CloseHandle(nint handle);

    [LibraryImport(Kernel)]
    private static partial uint WaitForSingleObject(SafeProcessHandle handle, uint milliseconds);
}
