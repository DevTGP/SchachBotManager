// The names of the constants are their documentation; spec/api/constants.json has no more.
#pragma warning disable CS1591

namespace Sbm;

/// <summary>
/// Bits of the castling rights (E35). Values of the type CastlingRights in spec/api/constants.json.
/// </summary>
public static class CastlingRights
{
    public const byte WhiteKingside = 1;
    public const byte WhiteQueenside = 2;
    public const byte BlackKingside = 4;
    public const byte BlackQueenside = 8;
    public const byte NoCastling = 0;
    public const byte AllCastling = 15;
}
