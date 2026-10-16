// The names of the constants are their documentation; spec/api/constants.json has no more.
#pragma warning disable CS1591

namespace Sbm;

/// <summary>
/// Flags of a move, bits 12 to 15 (E34). Values of the type MoveFlags in spec/api/constants.json.
/// </summary>
public static class MoveFlags
{
    public const byte Quiet = 0;
    public const byte DoublePawnPush = 1;
    public const byte KingCastle = 2;
    public const byte QueenCastle = 3;
    public const byte Capture = 4;
    public const byte EnPassant = 5;
    public const byte PromotionKnight = 8;
    public const byte PromotionBishop = 9;
    public const byte PromotionRook = 10;
    public const byte PromotionQueen = 11;
    public const byte PromotionCaptureKnight = 12;
    public const byte PromotionCaptureBishop = 13;
    public const byte PromotionCaptureRook = 14;
    public const byte PromotionCaptureQueen = 15;
}
