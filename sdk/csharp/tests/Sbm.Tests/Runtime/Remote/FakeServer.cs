using System.Collections.Concurrent;
using System.Globalization;
using System.Net;
using System.Net.Sockets;
using System.Net.WebSockets;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json.Nodes;

namespace Sbm.Tests.Runtime.Remote;

/// <summary>
/// The web API and the gateway in one listener, for remote tests (E116): POST
/// /api/v1/remote/matches answers with a seat, the WebSocket accepts one join and then plays
/// the referee's part of a game.
/// </summary>
internal sealed class FakeServer : IDisposable
{
    public const string Token = "sbm_AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA";
    public const string Seat = "Xq3v7dK2mP9sL1wR8tY4uB6nC0eF5gH2jA7kZ3xQ_-M";
    public const string MatchId = "6523a1f0c2d4e5f6a7b8c9d0";
    public const string SocketPath = "/api/v1/play/socket";

    public static readonly JsonObject[] Game =
    [
        Referee.Example("init.standard"),
        Referee.Example("turn.first_move"),
        Referee.Example("game_over.checkmate"),
    ];

    private const string Guid = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11";

    private readonly TcpListener _listener = new(IPAddress.Loopback, 0);
    private readonly CancellationTokenSource _stop = new();
    private int _disposed;
    private readonly Task _accepting;
    private readonly ConcurrentBag<Task> _connections = [];

    public FakeServer(JsonObject[]? game = null, TimeSpan? ping = null)
    {
        Messages = game ?? Game;
        Ping = ping;
        _listener.Start();
        _accepting = Task.Run(AcceptAsync);
    }

    public JsonObject[] Messages { get; }

    public TimeSpan? Ping { get; }

    /// <summary>The answer to POST: status code and body; the default gives a seat as white.</summary>
    public (int Status, string Body) Answer { get; set; } =
        (
            201,
            new JsonObject
            {
                ["match_id"] = MatchId,
                ["seat"] = Seat,
                ["color"] = "white",
                ["socket_path"] = SocketPath,
            }.ToJsonString()
        );

    /// <summary>Path, headers with lower-case names and body of each request for a game.</summary>
    public ConcurrentQueue<GameRequestSeen> Requests { get; } = [];

    /// <summary>The messages the client sent over the WebSocket.</summary>
    public ConcurrentQueue<JsonObject> Received { get; } = [];

    public int Port => ((IPEndPoint)_listener.LocalEndpoint).Port;

    public string Url => $"http://127.0.0.1:{Port}";

    public string SocketUrl => $"ws://127.0.0.1:{Port}{SocketPath}";

    public string[] ReceivedTypes() =>
        [.. Received.Select(message => Referee.Str(message, "type"))];

    public void Dispose()
    {
        if (Interlocked.Exchange(ref _disposed, 1) == 1)
        {
            return;
        }
        _stop.Cancel();
        _listener.Stop();
        try
        {
            Task.WaitAll([_accepting, .. _connections], TimeSpan.FromSeconds(5));
        }
        catch (AggregateException) { }
        _stop.Dispose();
    }

    private async Task AcceptAsync()
    {
        try
        {
            while (true)
            {
                var client = await _listener.AcceptTcpClientAsync(_stop.Token);
                _connections.Add(Task.Run(() => ServeAsync(client)));
            }
        }
        catch (Exception error) when (error is OperationCanceledException or SocketException) { }
    }

    private async Task ServeAsync(TcpClient client)
    {
        using (client)
        {
            var stream = client.GetStream();
            try
            {
                var (requestLine, headers) = await ReadHeadAsync(stream);
                var parts = requestLine.Split(' ');
                if (parts[0] == "POST")
                {
                    await AnswerAsync(stream, parts[1], headers);
                }
                else if (parts[1] == SocketPath)
                {
                    await PlayAsync(stream, headers);
                }
                else
                {
                    const string NotFound = "HTTP/1.1 404 Not Found\r\nContent-Length: 0\r\n\r\n";
                    await stream.WriteAsync(Encoding.ASCII.GetBytes(NotFound), _stop.Token);
                }
            }
            catch (Exception error) when (IsClosed(error)) { }
        }
    }

    private async Task<(string, Dictionary<string, string>)> ReadHeadAsync(Stream stream)
    {
        var head = new List<byte>();
        var one = new byte[1];
        while (!head.TakeLast(4).SequenceEqual("\r\n\r\n"u8.ToArray()))
        {
            if (await stream.ReadAsync(one, _stop.Token) == 0)
            {
                throw new IOException("the client closed the connection");
            }
            head.Add(one[0]);
        }
        var lines = Encoding.ASCII.GetString([.. head]).Split("\r\n");
        var headers = new Dictionary<string, string>();
        foreach (var line in lines.Skip(1).Where(line => line.Length > 0))
        {
            var colon = line.IndexOf(':', StringComparison.Ordinal);
            headers[line[..colon].Trim().ToLowerInvariant()] = line[(colon + 1)..].Trim();
        }
        return (lines[0], headers);
    }

    private async Task AnswerAsync(Stream stream, string path, Dictionary<string, string> headers)
    {
        var body = new byte[int.Parse(headers["content-length"], CultureInfo.InvariantCulture)];
        await stream.ReadExactlyAsync(body, _stop.Token);
        Requests.Enqueue(new GameRequestSeen(path, headers, JsonNode.Parse(body)!.AsObject()));
        var (status, answer) = Answer;
        var data = Encoding.UTF8.GetBytes(answer);
        var head =
            $"HTTP/1.1 {status} Fake\r\nContent-Type: application/json\r\n"
            + $"Content-Length: {data.Length}\r\nConnection: close\r\n\r\n";
        await stream.WriteAsync(Encoding.ASCII.GetBytes(head), _stop.Token);
        await stream.WriteAsync(data, _stop.Token);
    }

    private async Task PlayAsync(Stream stream, Dictionary<string, string> headers)
    {
        // SHA-1 is what RFC 6455 prescribes for the handshake.
#pragma warning disable CA5350
        var accept = Convert.ToBase64String(
            SHA1.HashData(Encoding.ASCII.GetBytes(headers["sec-websocket-key"] + Guid))
        );
#pragma warning restore CA5350
        var head =
            "HTTP/1.1 101 Switching Protocols\r\nUpgrade: websocket\r\nConnection: Upgrade\r\n"
            + $"Sec-WebSocket-Accept: {accept}\r\n\r\n";
        await stream.WriteAsync(Encoding.ASCII.GetBytes(head), _stop.Token);
        var options = new WebSocketCreationOptions { IsServer = true };
        if (Ping is { } ping)
        {
            options.KeepAliveInterval = ping;
            options.KeepAliveTimeout = ping;
        }
        using var socket = WebSocket.CreateFromStream(stream, options);
        var join = await ReceiveAsync(socket);
        Received.Enqueue(join);
        if (Referee.Str(join, "seat") != Seat)
        {
            await SendAsync(
                socket,
                new JsonObject
                {
                    ["type"] = "refused",
                    ["v"] = 1,
                    ["code"] = "no_game",
                    ["message"] = "?",
                }
            );
            return;
        }
        await SendAsync(
            socket,
            new JsonObject
            {
                ["type"] = "joined",
                ["v"] = 1,
                ["match_id"] = MatchId,
            }
        );
        foreach (var message in Messages)
        {
            await SendAsync(socket, message);
            if (Referee.Str(message, "type") is "init" or "turn")
            {
                Received.Enqueue(await ReceiveAsync(socket));
            }
        }
        await socket.CloseAsync(WebSocketCloseStatus.NormalClosure, null, _stop.Token);
    }

    private async Task<JsonObject> ReceiveAsync(WebSocket socket)
    {
        var buffer = new byte[65_536];
        var length = 0;
        ValueWebSocketReceiveResult result;
        do
        {
            result = await socket.ReceiveAsync(buffer.AsMemory(length), _stop.Token);
            length += result.Count;
        } while (!result.EndOfMessage);
        if (result.MessageType != WebSocketMessageType.Text)
        {
            throw new IOException("the client closed the WebSocket");
        }
        return JsonNode.Parse(buffer.AsSpan(0, length))!.AsObject();
    }

    private Task SendAsync(WebSocket socket, JsonObject message) =>
        socket.SendAsync(
            Encoding.UTF8.GetBytes(message.ToJsonString()),
            WebSocketMessageType.Text,
            true,
            _stop.Token
        );

    private static bool IsClosed(Exception error) =>
        error
            is IOException
                or WebSocketException
                or OperationCanceledException
                or ObjectDisposedException;
}

/// <summary>A request for a game as the fake server received it.</summary>
public sealed record GameRequestSeen(
    string Path,
    Dictionary<string, string> Headers,
    JsonObject Body
);
