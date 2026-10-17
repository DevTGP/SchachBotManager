using System.Text.Json;

namespace Sbm.Runtime.Viewer;

/// <summary>
/// The one viewer window of a bot program, fed with the games and log lines of the bot (E106).
/// Open starts the viewer once per program; games pick it up through Active, the log writes into
/// it as well. At the end, Run and Play keep the window open until the user closes it; ending
/// the process (e.g. in the IDE) closes it too. After a broken pipe it stays silent.
/// </summary>
internal sealed class ViewerWindow(IViewerProcess process)
{
    /// <summary>
    /// Set to a non-empty value, it keeps the window shut whatever the code asks for; the sandbox
    /// on the server sets it (E108).
    /// </summary>
    internal const string DisableVariable = "SBM_NO_VIEWER";

    private static readonly Lock Gate = new();
    private static ViewerWindow? _window;
    private static bool _missingReported;

    // Reentrant: a warning written while sending reaches Send again through the log.
    private readonly Lock _lock = new();
    private bool _sending;
    private volatile bool _open = true;
    private bool _botWhite = true;

    /// <summary>Where the program is looked for; for tests.</summary>
    internal static Func<string> FindProgram { get; set; } = ViewerProgram.Path;

    /// <summary>How the program is started; for tests.</summary>
    internal static Func<string, IViewerProcess> StartProgram { get; set; } = ViewerProgram.Start;

    /// <summary>The open viewer window of this program, if there is one.</summary>
    internal static ViewerWindow? Active => _window is { IsOpen: true } window ? window : null;

    internal bool IsOpen => _open && !process.HasExited;

    /// <summary>
    /// Opens the viewer window of this program, or returns the open one. Null if SBM_NO_VIEWER is
    /// set, the package carries no viewer or it cannot start; the bot then runs without a window.
    /// </summary>
    internal static ViewerWindow? Open(Func<string, string?> env)
    {
        lock (Gate)
        {
            if (Active is { } active)
            {
                return active;
            }
            if (!string.IsNullOrEmpty(env(DisableVariable)))
            {
                return null;
            }
            var path = FindProgram();
            var name = Path.GetFileName(path);
            if (!File.Exists(path))
            {
                if (!_missingReported)
                {
                    _missingReported = true;
                    Log.Warn($"viewer: {name} is not part of this installation; no window opens");
                }
                return null;
            }
            IViewerProcess started;
            try
            {
                started = StartProgram(path);
            }
            catch (Exception error) when (error is IOException or UnauthorizedAccessException)
            {
                Log.Warn($"viewer: cannot start {name}: {error.Message}");
                return null;
            }
            var window = new ViewerWindow(started);
            _window = window;
            Log.Listener = window.LogLine;
            return window;
        }
    }

    /// <summary>Forgets the window and its log listener; for tests.</summary>
    internal static void Reset()
    {
        lock (Gate)
        {
            _window = null;
            _missingReported = false;
            Log.Listener = null;
        }
    }

    internal void GameStarted(string bot, GameInfo info)
    {
        _botWhite = info.Color == Color.White;
        Send(json => ViewerMessages.Start(json, bot, info));
    }

    /// <summary>clocks: remaining times of the bot and of its opponent after the move.</summary>
    internal void MovePlayed(
        int ply,
        string uci,
        string fen,
        bool byBot,
        (long Bot, long Opponent)? clocks = null,
        long? elapsedMs = null,
        string? info = null
    )
    {
        (long, long)? colors = clocks is var (own, other)
            ? _botWhite
                ? (own, other)
                : (other, own)
            : null;
        Send(json => ViewerMessages.Move(json, ply, uci, fen, byBot, colors, elapsedMs, info));
    }

    /// <summary>The referee's game_over; its final move goes ahead as a move of the opponent.</summary>
    internal void GameOver(JsonElement gameOver)
    {
        if (
            gameOver.TryGetProperty("last_move", out var lastMove)
            && lastMove.ValueKind == JsonValueKind.String
            && gameOver.TryGetProperty("fen", out var fen)
            && fen.ValueKind == JsonValueKind.String
            && gameOver.TryGetProperty("ply", out var ply)
            && ply.ValueKind == JsonValueKind.Number
            && ply.TryGetInt32(out var number)
            && number > 0
        )
        {
            MovePlayed(number, lastMove.GetString()!, fen.GetString()!, byBot: false);
        }
        Send(gameOver.WriteTo);
    }

    internal void LogLine(byte level, string time, string text) =>
        Send(json => ViewerMessages.Log(json, level, time, text));

    /// <summary>Holds the program until the user closes the window.</summary>
    internal void WaitUntilClosed()
    {
        if (IsOpen)
        {
            Log.Info("viewer: the program ends when the viewer window is closed");
            process.WaitForExit();
        }
        Close();
    }

    internal void Close()
    {
        lock (_lock)
        {
            _open = false;
            try
            {
                process.Input.Dispose();
            }
            catch (IOException) { }
        }
    }

    internal void Send(Action<Utf8JsonWriter> write)
    {
        lock (_lock)
        {
            if (!_open || _sending)
            {
                return;
            }
            _sending = true;
            try
            {
                var line = JsonLines.Encode(write);
                process.Input.Write(line.Span);
                process.Input.Flush();
            }
            catch (Exception error) when (error is IOException or ObjectDisposedException)
            {
                // The user closed the window, or it never opened (no display).
                _open = false;
            }
            finally
            {
                _sending = false;
            }
        }
    }
}
