using System.Runtime.InteropServices;

namespace Sbm.Native;

/// <summary>board_state.h: end conditions; every result is an sbm_bool.</summary>
internal static partial class Core
{
    [LibraryImport(Library)]
    internal static partial int sbm_board_is_check(BoardHandle board, out int result);

    [LibraryImport(Library)]
    internal static partial int sbm_board_is_checkmate(BoardHandle board, out int result);

    [LibraryImport(Library)]
    internal static partial int sbm_board_is_stalemate(BoardHandle board, out int result);

    [LibraryImport(Library)]
    internal static partial int sbm_board_is_repetition(
        BoardHandle board,
        int count,
        out int result
    );

    [LibraryImport(Library)]
    internal static partial int sbm_board_is_fifty_move_rule(BoardHandle board, out int result);

    [LibraryImport(Library)]
    internal static partial int sbm_board_is_insufficient_material(
        BoardHandle board,
        out int result
    );

    [LibraryImport(Library)]
    internal static partial int sbm_board_has_insufficient_material(
        BoardHandle board,
        byte color,
        out int result
    );

    [LibraryImport(Library)]
    internal static partial int sbm_board_is_draw(BoardHandle board, out int result);

    [LibraryImport(Library)]
    internal static partial int sbm_board_is_game_over(BoardHandle board, out int result);
}
