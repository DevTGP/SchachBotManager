using Sbm.Native;

namespace Sbm;

/// <summary>Single properties of the position.</summary>
public sealed partial class Board
{
    private const int SquareCount = 64;

    /// <summary>The piece on a square, or <see cref="Piece.NoPiece"/>.</summary>
    /// <exception cref="InvalidArgumentException">The square is above 63.</exception>
    public byte PieceAt(byte square)
    {
        Status.Check(Core.sbm_board_piece_at(_handle, square, out var piece), "Board.PieceAt");
        return piece;
    }

    /// <summary>
    /// The pieces with their squares, ordered a1 to h8; of one color or both and of one type or
    /// all (<see cref="Color.NoColor"/> and <see cref="PieceType.NoPieceType"/> match all).
    /// </summary>
    /// <exception cref="InvalidArgumentException">The color or piece type is out of range.</exception>
    public unsafe PlacedPiece[] Pieces(
        byte color = Color.NoColor,
        byte pieceType = PieceType.NoPieceType
    )
    {
        var squares = stackalloc byte[SquareCount];
        var pieces = stackalloc byte[SquareCount];
        Status.Check(
            Core.sbm_board_pieces(
                _handle,
                color,
                pieceType,
                squares,
                pieces,
                SquareCount,
                out var count
            ),
            "Board.Pieces"
        );
        var placed = new PlacedPiece[count];
        for (var i = 0; i < placed.Length; i++)
        {
            placed[i] = new PlacedPiece(squares[i], pieces[i]);
        }
        return placed;
    }

    /// <summary>The color to move.</summary>
    public byte SideToMove()
    {
        Status.Check(Core.sbm_board_side_to_move(_handle, out var color), "Board.SideToMove");
        return color;
    }

    /// <summary>The remaining castling rights, one bit each of <see cref="CastlingRights"/>.</summary>
    public byte CastlingRights()
    {
        Status.Check(
            Core.sbm_board_castling_rights(_handle, out var rights),
            "Board.CastlingRights"
        );
        return rights;
    }

    /// <summary>
    /// The target square of a legal en passant capture, or <see cref="Square.NoSquare"/>.
    /// </summary>
    public byte EnPassantSquare()
    {
        Status.Check(
            Core.sbm_board_en_passant_square(_handle, out var square),
            "Board.EnPassantSquare"
        );
        return square;
    }

    /// <summary>Half moves since the last capture or pawn move.</summary>
    public int HalfmoveClock()
    {
        Status.Check(Core.sbm_board_halfmove_clock(_handle, out var clock), "Board.HalfmoveClock");
        return clock;
    }

    /// <summary>Starts at 1 and increases after each move of Black.</summary>
    public int FullmoveNumber()
    {
        Status.Check(
            Core.sbm_board_fullmove_number(_handle, out var number),
            "Board.FullmoveNumber"
        );
        return number;
    }

    /// <summary>The square of the king of that color.</summary>
    /// <exception cref="InvalidArgumentException">The color is out of range.</exception>
    public byte KingSquare(byte color)
    {
        Status.Check(
            Core.sbm_board_king_square(_handle, color, out var square),
            "Board.KingSquare"
        );
        return square;
    }
}
