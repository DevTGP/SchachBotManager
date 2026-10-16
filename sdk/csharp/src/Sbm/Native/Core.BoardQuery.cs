using System.Runtime.InteropServices;

namespace Sbm.Native;

/// <summary>board_query.h: single properties of the position.</summary>
internal static unsafe partial class Core
{
    [LibraryImport(Library)]
    internal static partial int sbm_board_piece_at(BoardHandle board, byte square, out byte piece);

    [LibraryImport(Library)]
    internal static partial int sbm_board_pieces(
        BoardHandle board,
        byte color,
        byte pieceType,
        byte* squares,
        byte* pieces,
        uint capacity,
        out uint count
    );

    [LibraryImport(Library)]
    internal static partial int sbm_board_side_to_move(BoardHandle board, out byte color);

    [LibraryImport(Library)]
    internal static partial int sbm_board_castling_rights(BoardHandle board, out byte rights);

    [LibraryImport(Library)]
    internal static partial int sbm_board_en_passant_square(BoardHandle board, out byte square);

    [LibraryImport(Library)]
    internal static partial int sbm_board_halfmove_clock(BoardHandle board, out int clock);

    [LibraryImport(Library)]
    internal static partial int sbm_board_fullmove_number(BoardHandle board, out int number);

    [LibraryImport(Library)]
    internal static partial int sbm_board_king_square(
        BoardHandle board,
        byte color,
        out byte square
    );
}
