using System.Runtime.InteropServices;

namespace Sbm.Native;

/// <summary>move.h: UCI text of moves.</summary>
internal static unsafe partial class Core
{
    [LibraryImport(Library, StringMarshalling = StringMarshalling.Utf8)]
    internal static partial int sbm_move_parse(string uci, out ushort move);

    [LibraryImport(Library)]
    internal static partial int sbm_move_uci(ushort move, byte* buffer, uint size);
}
