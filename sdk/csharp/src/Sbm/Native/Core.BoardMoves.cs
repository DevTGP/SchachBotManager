using System.Runtime.InteropServices;

namespace Sbm.Native;

/// <summary>board_moves.h: generating, checking, making and taking back moves; SAN.</summary>
internal static unsafe partial class Core
{
    [LibraryImport(Library)]
    internal static partial int sbm_board_legal_moves(
        BoardHandle board,
        ushort* moves,
        uint capacity,
        out uint count
    );

    [LibraryImport(Library)]
    internal static partial int sbm_board_legal_captures(
        BoardHandle board,
        ushort* moves,
        uint capacity,
        out uint count
    );

    [LibraryImport(Library)]
    internal static partial int sbm_board_all_moves_from(
        BoardHandle board,
        byte square,
        ushort* moves,
        uint capacity,
        out uint count
    );

    [LibraryImport(Library)]
    internal static partial int sbm_board_is_legal(BoardHandle board, ushort move, out int legal);

    [LibraryImport(Library, StringMarshalling = StringMarshalling.Utf8)]
    internal static partial int sbm_board_parse_move(
        BoardHandle board,
        string uci,
        out ushort move
    );

    [LibraryImport(Library)]
    internal static partial int sbm_board_san(
        BoardHandle board,
        ushort move,
        byte* buffer,
        uint size
    );

    [LibraryImport(Library)]
    internal static partial int sbm_board_make_move(BoardHandle board, ushort move);

    [LibraryImport(Library)]
    internal static partial int sbm_board_undo_move(BoardHandle board);

    [LibraryImport(Library)]
    internal static partial int sbm_board_make_null_move(BoardHandle board);

    [LibraryImport(Library)]
    internal static partial int sbm_board_undo_null_move(BoardHandle board);
}
