using System.Runtime.InteropServices;

namespace Sbm.Native;

/// <summary>Text across the C boundary: NUL-terminated ASCII in buffers of fixed size (E51).</summary>
internal static unsafe class Text
{
    internal const int FenBufferSize = 128;
    internal const int UciBufferSize = 6;
    internal const int SanBufferSize = 16;
    internal const int TextBufferSize = 512;

    /// <summary>A NUL-terminated text of the core.</summary>
    internal static string FromC(byte* text) =>
        Marshal.PtrToStringUTF8((IntPtr)text) ?? string.Empty;

    /// <summary>Strings with an embedded NUL would be cut short at the C boundary.</summary>
    internal static bool HasNul(string? text) => text is not null && text.Contains('\0');

    internal static string Name(int status) => FromC(Core.sbm_status_name(status));

    /// <summary>A string argument as it appears in messages, e.g. <c>"e2e5"</c>.</summary>
    internal static string Quote(string text) =>
        "\"" + text.Replace("\"", "\\\"", StringComparison.Ordinal) + "\"";
}
