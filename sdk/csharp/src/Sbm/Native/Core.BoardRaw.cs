using System.Runtime.InteropServices;

namespace Sbm.Native;

/// <summary>board_raw.h: bitboards and squares.</summary>
internal static unsafe partial class Core
{
    [LibraryImport(Library)]
    internal static partial int sbm_board_bitboard(
        BoardHandle board,
        byte color,
        byte pieceType,
        out ulong bitboard
    );

    [LibraryImport(Library)]
    internal static partial int sbm_board_bitboards(BoardHandle board, ulong* bitboards);

    [LibraryImport(Library)]
    internal static partial int sbm_board_squares(BoardHandle board, byte* pieces);

    [LibraryImport(Library)]
    internal static partial int sbm_board_occupied(BoardHandle board, out ulong bitboard);

    [LibraryImport(Library)]
    internal static partial int sbm_board_occupied_by(
        BoardHandle board,
        byte color,
        out ulong bitboard
    );

    [LibraryImport(Library)]
    internal static partial int sbm_board_piece_count(
        BoardHandle board,
        byte color,
        byte pieceType,
        out int count
    );

    [LibraryImport(Library)]
    internal static partial int sbm_board_attacks_from(
        BoardHandle board,
        byte square,
        out ulong bitboard
    );

    [LibraryImport(Library)]
    internal static partial int sbm_board_attackers_of(
        BoardHandle board,
        byte square,
        byte color,
        out ulong bitboard
    );

    [LibraryImport(Library)]
    internal static partial int sbm_board_is_attacked(
        BoardHandle board,
        byte square,
        byte color,
        out int attacked
    );

    [LibraryImport(Library)]
    internal static partial int sbm_board_checkers(BoardHandle board, out ulong bitboard);

    [LibraryImport(Library)]
    internal static partial int sbm_board_pinned(BoardHandle board, byte color, out ulong bitboard);
}
