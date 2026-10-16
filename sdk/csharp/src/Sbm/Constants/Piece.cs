// The names of the constants are their documentation; spec/api/constants.json has no more.
#pragma warning disable CS1591

namespace Sbm;

/// <summary>
/// Pieces: color * 6 + piece type (E35). Values of the type Piece in spec/api/constants.json.
/// </summary>
public static class Piece
{
    public const byte WhitePawn = 0;
    public const byte WhiteKnight = 1;
    public const byte WhiteBishop = 2;
    public const byte WhiteRook = 3;
    public const byte WhiteQueen = 4;
    public const byte WhiteKing = 5;
    public const byte BlackPawn = 6;
    public const byte BlackKnight = 7;
    public const byte BlackBishop = 8;
    public const byte BlackRook = 9;
    public const byte BlackQueen = 10;
    public const byte BlackKing = 11;

    /// <summary>Empty square.</summary>
    public const byte NoPiece = 12;
}
