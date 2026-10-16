using Sbm.Runtime;

namespace Sbm.Tests.Runtime;

/// <summary>Collects the log lines of a test and restores the default log afterwards.</summary>
internal sealed class LogCapture : IDisposable
{
    private readonly StringWriter _lines = new();

    public LogCapture(byte level = LogLevel.Info)
    {
        Log.Configure(level, null);
        Log.SetPly(null);
        Log.Output = _lines;
    }

    public string Text => _lines.ToString();

    public void Dispose()
    {
        Log.Output = null;
        Log.Configure(LogLevel.Info, null);
        Log.SetPly(null);
        _lines.Dispose();
    }
}
