using System.Text;
using System.Text.Json;
using System.Text.Json.Nodes;
using Sbm.Runtime.Referee;

namespace Sbm.Tests.Runtime.Matches;

/// <summary>Monotonic nanoseconds that only move when a scripted answer takes time.</summary>
internal sealed class FakeTime
{
    public long Ns { get; set; }

    public long Now() => Ns;
}

/// <summary>
/// One line after AfterMs. Without Waiting the line is lost if it comes after the deadline; with
/// Waiting it is returned anyway, as an adapter returns a buffered line.
/// </summary>
internal sealed record Reply(object Line, long AfterMs = 0, bool Waiting = false);

/// <summary>A line the bot sent outside its turn; the referee finds it when it polls.</summary>
internal sealed record Early(object Line);

/// <summary>One call of the referee: Kind is the method, Message the sent one, Deadline the wait.</summary>
internal sealed record PlayerEvent(string Kind, JsonObject? Message = null, long? Deadline = null);

/// <summary>
/// A player that answers from a script on a fake clock, as in the tests of the Python SDK. Each
/// receive takes the next item: a JsonObject or bytes is answered at once, a Reply after its
/// time, an exception is thrown. Events records every call of the referee.
/// </summary>
internal class ScriptedPlayer(string name, FakeTime time, params object[] script) : Player(name)
{
    public const long NsPerMs = GameClock.NanosecondsPerMs;

    private readonly Queue<object> _script = new(script);
    private bool _alive = true;

    public List<PlayerEvent> Events { get; } = [];

    public List<JsonObject> Sent =>
        [.. Events.Where(item => item.Kind == "send").Select(item => item.Message!)];

    public string[] SentTypes() => [.. Sent.Select(message => Referee.Str(message, "type"))];

    public long?[] Deadlines() =>
        [.. Events.Where(item => item.Kind == "receive").Select(item => item.Deadline)];

    public static JsonObject Ready(string sdk = "1.0.0", string lang = "python") =>
        new()
        {
            ["type"] = "ready",
            ["v"] = 1,
            ["sdk"] = sdk,
            ["lang"] = lang,
        };

    public static JsonObject Move(string uci) =>
        new()
        {
            ["type"] = "move",
            ["v"] = 1,
            ["move"] = uci,
        };

    public static JsonObject Resign() => new() { ["type"] = "resign", ["v"] = 1 };

    internal override void Start() => Events.Add(new("start"));

    internal override void Send(Action<Utf8JsonWriter> message)
    {
        if (!_alive)
        {
            throw new PlayerClosedException("already gone");
        }
        var buffer = new MemoryStream();
        using (var json = new Utf8JsonWriter(buffer))
        {
            message(json);
        }
        Events.Add(new("send", JsonNode.Parse(buffer.ToArray())!.AsObject()));
    }

    internal override byte[] Receive(long? deadlineNs)
    {
        Events.Add(new("receive", Deadline: deadlineNs));
        _script.TryPeek(out var item);
        var polling = deadlineNs is { } limit && limit <= time.Ns;
        if (polling && item is not Early)
        {
            throw new PlayerTimeoutException();
        }
        if (item is null)
        {
            throw new InvalidOperationException($"{Name}: script exhausted");
        }
        _script.Dequeue();
        switch (item)
        {
            case PlayerClosedException closed:
                _alive = false;
                throw closed;
            case Exception error:
                throw error;
            case Early early:
                return Bytes(early.Line);
        }
        var reply = item as Reply ?? new Reply(item);
        time.Ns += reply.AfterMs * NsPerMs;
        if (deadlineNs is { } deadline && time.Ns > deadline && !reply.Waiting)
        {
            time.Ns = deadline;
            throw new PlayerTimeoutException();
        }
        return Bytes(reply.Line);
    }

    internal override void Suspend() => Events.Add(new("suspend"));

    internal override void Resume()
    {
        if (!_alive)
        {
            throw new PlayerClosedException("already gone");
        }
        Events.Add(new("resume"));
    }

    protected override void Dispose(bool disposing)
    {
        Events.Add(new("close"));
        base.Dispose(disposing);
    }

    private static byte[] Bytes(object line) =>
        line as byte[] ?? Encoding.UTF8.GetBytes(((JsonObject)line).ToJsonString());
}
