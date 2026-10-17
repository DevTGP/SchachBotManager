using System.Globalization;

namespace Sbm;

/// <summary>
/// Debug log of the bot with the levels of <see cref="LogLevel"/>, written to stderr. Each line
/// carries time, ply and level: <c>14:03:27.512 [ply 12] INFO  message</c>. The SDK sets the
/// start level and an optional file from the command line or environment (E61) and the ply from
/// each turn. Safe to call from several threads.
/// </summary>
public static class Log
{
    private static readonly string[] LevelNames = ["TRACE", "DEBUG", "INFO", "WARN", "ERROR"];
    private static readonly Lock Gate = new();
    private static byte _level = LogLevel.Info;
    private static int? _ply;
    private static TextWriter? _file;

    // Set on the threads of the reference bots of Sdk.Play, whose log the user does not see.
    [ThreadStatic]
    private static bool t_muted;

    /// <summary>Where lines go instead of stderr; for tests.</summary>
    internal static TextWriter? Output { get; set; }

    /// <summary>Receives level, time and text of every written line: the viewer window (E106).</summary>
    internal static Action<byte, string, string>? Listener { get; set; }

    /// <summary>Whether the log of the current thread is dropped, ply included.</summary>
    internal static bool Muted
    {
        get => t_muted;
        set => t_muted = value;
    }

    /// <summary>Writes at level TRACE.</summary>
    public static void Trace(string message) => Write(LogLevel.Trace, message);

    /// <summary>Writes at level DEBUG.</summary>
    public static void Debug(string message) => Write(LogLevel.Debug, message);

    /// <summary>Writes at level INFO.</summary>
    public static void Info(string message) => Write(LogLevel.Info, message);

    /// <summary>Writes at level WARN.</summary>
    public static void Warn(string message) => Write(LogLevel.Warn, message);

    /// <summary>Writes at level ERROR.</summary>
    public static void Error(string message) => Write(LogLevel.Error, message);

    /// <summary>Sets the minimum level written; <see cref="LogLevel.Off"/> writes nothing.</summary>
    public static void SetLevel(byte level) => _level = Check("Log.SetLevel", level);

    /// <summary>Current minimum level; INFO unless the command line or environment says otherwise.</summary>
    public static byte Level() => _level;

    /// <summary>Whether a message at that level would be written.</summary>
    public static bool IsEnabled(byte level) =>
        _level <= Check("Log.IsEnabled", level) && level < LogLevel.Off;

    /// <summary>Start level and optional log file, set by Run before the game.</summary>
    internal static void Configure(byte level, TextWriter? file)
    {
        lock (Gate)
        {
            _level = level;
            _file = file;
        }
    }

    /// <summary>Ply shown in each line from the current turn on.</summary>
    internal static void SetPly(int? ply)
    {
        if (!t_muted)
        {
            _ply = ply;
        }
    }

    private static byte Check(string function, byte level) =>
        level <= LogLevel.Off
            ? level
            : throw new InvalidArgumentException($"{function}: unknown level {level}");

    private static void Write(byte level, string message)
    {
        if (level < _level || t_muted)
        {
            return;
        }
        var time = DateTime.Now.ToString("HH:mm:ss.fff", CultureInfo.InvariantCulture);
        var ply = _ply is { } number ? number.ToString(CultureInfo.InvariantCulture) : "-";
        var line = $"{time} [ply {ply}] {LevelNames[level].PadRight(5)} {message}\n";
        lock (Gate)
        {
            var output = Output ?? Console.Error;
            output.Write(line);
            output.Flush();
            if (_file is not null)
            {
                _file.Write(line);
                _file.Flush();
            }
        }
        Listener?.Invoke(level, time, message);
    }
}
