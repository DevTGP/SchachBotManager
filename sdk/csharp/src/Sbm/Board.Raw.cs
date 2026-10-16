using Sbm.Native;

namespace Sbm;

/// <summary>Raw access: bitboards and squares; bit i of a bitboard stands for square i.</summary>
public sealed partial class Board
{
    private const int PieceKinds = 12;

    /// <summary>The squares with pieces of that color and type.</summary>
    /// <exception cref="InvalidArgumentException">The color or piece type is out of range.</exception>
    public ulong Bitboard(byte color, byte pieceType)
    {
        Status.Check(
            Core.sbm_board_bitboard(_handle, color, pieceType, out var bitboard),
            "Board.Bitboard"
        );
        return bitboard;
    }

    /// <summary>All 12 piece bitboards, indexed by <see cref="Piece"/>.</summary>
    public unsafe ulong[] Bitboards()
    {
        var bitboards = new ulong[PieceKinds];
        fixed (ulong* pointer = bitboards)
        {
            Status.Check(Core.sbm_board_bitboards(_handle, pointer), "Board.Bitboards");
        }
        return bitboards;
    }

    /// <summary>
    /// The 64 squares, indexed by <see cref="Square"/>; <see cref="Piece.NoPiece"/> on empty ones.
    /// </summary>
    public unsafe byte[] Squares()
    {
        var pieces = new byte[SquareCount];
        fixed (byte* pointer = pieces)
        {
            Status.Check(Core.sbm_board_squares(_handle, pointer), "Board.Squares");
        }
        return pieces;
    }

    /// <summary>All occupied squares.</summary>
    public ulong Occupied()
    {
        Status.Check(Core.sbm_board_occupied(_handle, out var bitboard), "Board.Occupied");
        return bitboard;
    }

    /// <summary>The squares occupied by that color.</summary>
    /// <exception cref="InvalidArgumentException">The color is out of range.</exception>
    public ulong OccupiedBy(byte color)
    {
        Status.Check(
            Core.sbm_board_occupied_by(_handle, color, out var bitboard),
            "Board.OccupiedBy"
        );
        return bitboard;
    }

    /// <summary>The number of pieces of that color and type.</summary>
    /// <exception cref="InvalidArgumentException">The color or piece type is out of range.</exception>
    public int PieceCount(byte color, byte pieceType)
    {
        Status.Check(
            Core.sbm_board_piece_count(_handle, color, pieceType, out var count),
            "Board.PieceCount"
        );
        return count;
    }

    /// <summary>
    /// The squares the piece on that square attacks, own pieces included; pins are ignored.
    /// </summary>
    /// <exception cref="InvalidArgumentException">The square is above 63.</exception>
    public ulong AttacksFrom(byte square)
    {
        Status.Check(
            Core.sbm_board_attacks_from(_handle, square, out var bitboard),
            "Board.AttacksFrom"
        );
        return bitboard;
    }

    /// <summary>The pieces of that color that attack the square; pins are ignored.</summary>
    /// <exception cref="InvalidArgumentException">The square or color is out of range.</exception>
    public ulong AttackersOf(byte square, byte color)
    {
        Status.Check(
            Core.sbm_board_attackers_of(_handle, square, color, out var bitboard),
            "Board.AttackersOf"
        );
        return bitboard;
    }

    /// <summary>Whether a piece of that color attacks the square.</summary>
    /// <exception cref="InvalidArgumentException">The square or color is out of range.</exception>
    public bool IsAttacked(byte square, byte color)
    {
        Status.Check(
            Core.sbm_board_is_attacked(_handle, square, color, out var attacked),
            "Board.IsAttacked"
        );
        return attacked != 0;
    }

    /// <summary>The pieces giving check to the side to move.</summary>
    public ulong Checkers()
    {
        Status.Check(Core.sbm_board_checkers(_handle, out var bitboard), "Board.Checkers");
        return bitboard;
    }

    /// <summary>The pieces of that color pinned to their own king.</summary>
    /// <exception cref="InvalidArgumentException">The color is out of range.</exception>
    public ulong Pinned(byte color)
    {
        Status.Check(Core.sbm_board_pinned(_handle, color, out var bitboard), "Board.Pinned");
        return bitboard;
    }
}
