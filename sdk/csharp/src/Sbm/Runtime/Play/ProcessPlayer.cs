using System.ComponentModel;
using System.Diagnostics;
using Sbm.Runtime.Referee;

namespace Sbm.Runtime.Play;

/// <summary>
/// A bot as a local process for Sdk.Play: lines over stdin and stdout, its log from stderr
/// discarded, since it would mix with the own one. It is not frozen outside its turn; the own
/// bot in a thread cannot be frozen either.
/// </summary>
internal sealed class ProcessPlayer(string name, string program, IReadOnlyList<string> arguments)
    : StreamPlayer(name)
{
    // Time a bot gets to end on its own after game_over, and to report its exit code.
    private static readonly TimeSpan Grace = TimeSpan.FromSeconds(2);
    private static readonly TimeSpan ExitWait = TimeSpan.FromMilliseconds(500);

    private Process? _process;

    internal override void Start()
    {
        var start = new ProcessStartInfo(program, arguments)
        {
            RedirectStandardInput = true,
            RedirectStandardOutput = true,
            RedirectStandardError = true,
            UseShellExecute = false,
        };
        try
        {
            _process = Process.Start(start)!;
        }
        catch (Win32Exception error)
        {
            var command = PyText.Repr([program, .. arguments]);
            throw new PlayerClosedException($"cannot start {command}: {error.Message}");
        }
        // Read and dropped, so a bot that logs a lot does not block on a full pipe.
        _process.ErrorDataReceived += (_, _) => { };
        _process.BeginErrorReadLine();
        Attach(_process.StandardOutput.BaseStream, _process.StandardInput.BaseStream);
    }

    protected override PlayerClosedException Closed() =>
        _process!.WaitForExit(ExitWait)
            ? new($"the bot exited with code {_process.ExitCode}")
            : base.Closed();

    protected override void Dispose(bool disposing)
    {
        if (disposing && _process is { } process)
        {
            Stop(process);
        }
        base.Dispose(disposing);
    }

    private void Stop(Process process)
    {
        try
        {
            process.StandardInput.Close();
        }
        catch (IOException) { }
        if (Finished)
        {
            process.WaitForExit(Grace);
        }
        try
        {
            // Also processes the bot started and left behind.
            process.Kill(entireProcessTree: true);
        }
        catch (Exception error) when (error is InvalidOperationException or Win32Exception) { }
        process.WaitForExit();
        process.Dispose();
    }
}
