using System.Runtime.InteropServices;

namespace Sbm.Native;

/// <summary>board.h: creating, copying and freeing boards; FEN, hash, history, text.</summary>
internal static unsafe partial class Core
{
    [LibraryImport(Library)]
    internal static partial int sbm_board_new(out BoardHandle board);

    [LibraryImport(Library, StringMarshalling = StringMarshalling.Utf8)]
    internal static partial int sbm_board_from_fen(string fen, out BoardHandle board);

    [LibraryImport(Library)]
    internal static partial int sbm_board_copy(BoardHandle board, out BoardHandle copy);

    [LibraryImport(Library)]
    internal static partial void sbm_board_free(IntPtr board);

    [LibraryImport(Library)]
    internal static partial int sbm_board_fen(BoardHandle board, byte* buffer, uint size);

    [LibraryImport(Library)]
    internal static partial int sbm_board_hash(BoardHandle board, out ulong hash);

    [LibraryImport(Library)]
    internal static partial int sbm_board_move_history(
        BoardHandle board,
        ushort* moves,
        uint capacity,
        out uint count
    );

    [LibraryImport(Library)]
    internal static partial int sbm_board_to_text(BoardHandle board, byte* buffer, uint size);
}
