namespace Sbm.Runtime.Viewer;

/// <summary>The running viewer program: its stdin and whether it still runs.</summary>
internal interface IViewerProcess
{
    /// <summary>One JSON message per line; the program ends when this stream is closed.</summary>
    Stream Input { get; }

    bool HasExited { get; }

    void WaitForExit();
}
