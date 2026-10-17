using System.Collections.Concurrent;
using System.Net.WebSockets;

namespace Sbm.Runtime.Remote;

/// <summary>
/// A WebSocket to the gateway for text messages. A reader in the background receives all the
/// time, so pings are answered also while the bot thinks; a bot that is not reading would
/// otherwise be dropped by the gateway's keep-alive.
/// </summary>
internal sealed class RemoteSocket : IDisposable
{
    internal const int MaxMessageBytes = 4 * 65_536 + 1024;
    private static readonly TimeSpan ConnectTimeout = TimeSpan.FromSeconds(10);
    private static readonly TimeSpan CloseTimeout = TimeSpan.FromSeconds(2);

    private readonly WebSocket _socket;
    private readonly BlockingCollection<byte[]> _messages = [];
    private readonly Lock _sending = new();
    private readonly Task _reader;

    internal RemoteSocket(WebSocket socket)
    {
        _socket = socket;
        _reader = Task.Run(ReadMessagesAsync);
    }

    /// <summary>Opens ws:// or wss:// and does the opening handshake.</summary>
    internal static RemoteSocket Connect(string url)
    {
        var socket = new ClientWebSocket();
        socket.Options.SetRequestHeader("User-Agent", GameRequest.UserAgent);
        try
        {
            using var timeout = new CancellationTokenSource(ConnectTimeout);
            socket.ConnectAsync(new Uri(url), timeout.Token).GetAwaiter().GetResult();
        }
        catch (OperationCanceledException)
        {
            socket.Dispose();
            throw new WebSocketException($"no connection to {url} within {ConnectTimeout}");
        }
        catch
        {
            socket.Dispose();
            throw;
        }
        return new RemoteSocket(socket);
    }

    /// <summary>
    /// The next text message, null once the connection is closed; throws TimeoutException if
    /// none comes within timeout.
    /// </summary>
    internal byte[]? Receive(TimeSpan? timeout = null)
    {
        try
        {
            if (
                _messages.TryTake(
                    out var message,
                    timeout ?? System.Threading.Timeout.InfiniteTimeSpan
                )
            )
            {
                return message;
            }
        }
        catch (InvalidOperationException)
        {
            // Completed while waiting.
        }
        if (_messages.IsCompleted)
        {
            return null;
        }
        throw new TimeoutException("no message within the time");
    }

    internal void Send(ReadOnlySpan<byte> text)
    {
        var data = text.ToArray();
        lock (_sending)
        {
            try
            {
                _socket
                    .SendAsync(data, WebSocketMessageType.Text, true, CancellationToken.None)
                    .GetAwaiter()
                    .GetResult();
            }
            catch (Exception error) when (error is WebSocketException or ObjectDisposedException)
            {
                throw new IOException(
                    $"the connection to the server is lost: {error.Message}",
                    error
                );
            }
        }
    }

    /// <summary>Starts the closing handshake and waits briefly for the reader to finish.</summary>
    public void Dispose()
    {
        try
        {
            using var timeout = new CancellationTokenSource(CloseTimeout);
            _socket
                .CloseOutputAsync(WebSocketCloseStatus.NormalClosure, null, timeout.Token)
                .GetAwaiter()
                .GetResult();
        }
        catch (Exception error)
            when (error
                    is WebSocketException
                        or OperationCanceledException
                        or ObjectDisposedException
                        or InvalidOperationException
            )
        {
            // Already closed or broken.
        }
        _reader.Wait(CloseTimeout);
        _socket.Dispose();
        _messages.Dispose();
    }

    private async Task ReadMessagesAsync()
    {
        var buffer = new byte[MaxMessageBytes + 1];
        try
        {
            while (true)
            {
                var length = 0;
                ValueWebSocketReceiveResult result;
                do
                {
                    result = await _socket
                        .ReceiveAsync(buffer.AsMemory(length), CancellationToken.None)
                        .ConfigureAwait(false);
                    length += result.Count;
                } while (
                    !result.EndOfMessage
                    && result.MessageType == WebSocketMessageType.Text
                    && length < buffer.Length
                );
                // Close, binary messages, which are not part of the protocol, or too large.
                if (result.MessageType != WebSocketMessageType.Text || length > MaxMessageBytes)
                {
                    return;
                }
                _messages.Add(buffer[..length]);
            }
        }
        catch (Exception error)
            when (error is WebSocketException or ObjectDisposedException or IOException)
        {
            // The connection is gone.
        }
        finally
        {
            _messages.CompleteAdding();
        }
    }
}
