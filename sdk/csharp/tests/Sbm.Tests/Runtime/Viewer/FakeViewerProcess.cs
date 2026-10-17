using System.Text;
using System.Text.Json.Nodes;
using Sbm.Runtime.Viewer;

namespace Sbm.Tests.Runtime.Viewer;

/// <summary>A viewer process that records what the SDK writes, instead of opening a window.</summary>
internal sealed class FakeViewerProcess : IViewerProcess, IDisposable
{
    private readonly RecordingStream _input = new();

    public Stream Input => _input;

    /// <summary>Writes fail as after the user closed the window.</summary>
    public bool Broken
    {
        get => _input.Broken;
        set => _input.Broken = value;
    }

    public bool HasExited { get; set; }

    public bool Waited { get; private set; }

    public bool InputClosed => _input.Closed;

    public void Dispose() => _input.Dispose();

    public void WaitForExit()
    {
        Waited = true;
        HasExited = true;
    }

    public List<JsonObject> Messages() =>
        [
            .. Encoding
                .UTF8.GetString(_input.ToArray())
                .Split('\n', StringSplitOptions.RemoveEmptyEntries)
                .Select(line => JsonNode.Parse(line)!.AsObject()),
        ];

    public IEnumerable<string> Types() => Messages().Select(message => Referee.Str(message, "type"));

    private sealed class RecordingStream : MemoryStream
    {
        public bool Broken { get; set; }

        public bool Closed { get; private set; }

        public override void Write(ReadOnlySpan<byte> buffer)
        {
            if (Broken)
            {
                throw new IOException("the window was closed");
            }
            base.Write(buffer);
        }

        protected override void Dispose(bool disposing)
        {
            Closed = true;
            base.Dispose(disposing);
        }
    }
}
