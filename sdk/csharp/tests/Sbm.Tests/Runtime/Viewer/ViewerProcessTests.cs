using System.Text;
using Sbm.Runtime.Viewer;

namespace Sbm.Tests.Runtime.Viewer;

/// <summary>
/// Starting the viewer as a process of its own, with a stand-in program that reads its input to
/// the end: a shell script on Unix, sort.exe on Windows.
/// </summary>
public sealed class ViewerProcessTests : IDisposable
{
    private readonly string _dir = Directory.CreateTempSubdirectory("sbm-viewer-").FullName;

    public void Dispose() => Directory.Delete(_dir, recursive: true);

    [Fact]
    public void ReadsTheInputAndEndsWithIt()
    {
        var output = Path.Combine(_dir, "received");
        var process = ViewerProgram.Start(StandIn(output));
        Assert.False(process.HasExited);
        process.Input.Write("{\"type\":\"log\"}\n"u8);
        process.Input.Flush();
        process.Input.Dispose();
        WaitForExit(process);
        Assert.True(process.HasExited);
        if (!OperatingSystem.IsWindows())
        {
            Assert.Equal("{\"type\":\"log\"}\n", File.ReadAllText(output, Encoding.UTF8));
        }
    }

    [Fact]
    public void MissingProgramCannotStart()
    {
        var path = Path.Combine(_dir, ViewerProgram.Name);
        Assert.ThrowsAny<IOException>(() => ViewerProgram.Start(path));
    }

    [Fact]
    public void RunsInASessionOfItsOwn()
    {
        Assert.SkipWhen(OperatingSystem.IsWindows(), "sessions are a Unix matter");
        // A new session also leads a new process group; ps of macOS shows no session id.
        var field = OperatingSystem.IsMacOS() ? "pgid" : "sid";
        var output = Path.Combine(_dir, "session");
        var script = Script($"echo $$ $(ps -o {field}= -p $$) > \"{output}\"; cat > /dev/null");
        var process = ViewerProgram.Start(script);
        process.Input.Dispose();
        WaitForExit(process);
        var ids = File.ReadAllText(output).Split(' ', StringSplitOptions.TrimEntries);
        Assert.Equal(ids[0], ids[1]);
    }

    private string StandIn(string output) =>
        OperatingSystem.IsWindows()
            ? Path.Combine(Environment.SystemDirectory, "sort.exe")
            : Script($"cat > \"{output}\"");

    // NuGet drops the executable bit, so the script is written without it.
    private string Script(string body)
    {
        var path = Path.Combine(_dir, ViewerProgram.Name);
        File.WriteAllText(path, $"#!/bin/sh\n{body}\n");
        return path;
    }

    private static void WaitForExit(IViewerProcess process)
    {
        var waiting = Task.Run(process.WaitForExit);
        Assert.True(waiting.Wait(TimeSpan.FromSeconds(30)), "the program did not end");
    }
}
