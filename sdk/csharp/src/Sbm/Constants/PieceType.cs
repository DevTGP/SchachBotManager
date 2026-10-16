// The names of the constants are their documentation; spec/api/constants.json has no more.
#pragma warning disable CS1591

namespace Sbm;

/// <summary>
/// Piece types (E35). Values of the type PieceType in spec/api/constants.json.
/// </summary>
public static class PieceType
{
    public const byte Pawn = 0;
    public const byte Knight = 1;
    public const byte Bishop = 2;
    public const byte Rook = 3;
    public const byte Queen = 4;
    public const byte King = 5;

    /// <summary>No piece type, e.g. the promotion of a move that is no promotion.</summary>
    public const byte NoPieceType = 6;
}
