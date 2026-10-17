using System.Runtime.InteropServices;

namespace Sbm.Runtime.Viewer;

/// <summary>
/// The viewer program shipped in the NuGet package under runtimes/&lt;rid&gt;/native/ (E206),
/// started as a process of its own. It reads one JSON message per line from stdin and ends when
/// stdin ends, so the window stays open as long as the bot program holds the pipe.
/// </summary>
internal static class ViewerProgram
{
    internal static readonly string Name = OperatingSystem.IsWindows()
        ? "sbm-viewer.exe"
        : "sbm-viewer";

    /// <summary>
    /// Next to the assembly when the build copied the native files of one platform, otherwise in
    /// the folder of the current platform.
    /// </summary>
    internal static string Path()
    {
        var flat = System.IO.Path.Combine(AppContext.BaseDirectory, Name);
        if (File.Exists(flat))
        {
            return flat;
        }
        return System.IO.Path.Combine(
            AppContext.BaseDirectory,
            "runtimes",
            RuntimeInformation.RuntimeIdentifier,
            "native",
            Name
        );
    }

    /// <summary>Starts the viewer; IOException if it cannot run.</summary>
    internal static IViewerProcess Start(string path)
    {
        if (OperatingSystem.IsWindows())
        {
            return WindowsViewerProcess.Start(path);
        }
        MakeExecutable(path);
        return UnixViewerProcess.Start(path);
    }

    /// <summary>NuGet does not keep the permissions of the files in a package.</summary>
    [System.Runtime.Versioning.UnsupportedOSPlatform("windows")]
    private static void MakeExecutable(string path)
    {
        var mode = File.GetUnixFileMode(path);
        if ((mode & UnixFileMode.UserExecute) == 0)
        {
            File.SetUnixFileMode(path, mode | UnixFileMode.UserExecute);
        }
    }
}
