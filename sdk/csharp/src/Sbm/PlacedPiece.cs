namespace Sbm;

/// <summary>A piece on its square, as listed by <see cref="Board.Pieces"/> (E190).</summary>
/// <param name="Square">Square of the piece.</param>
/// <param name="Piece">The piece.</param>
public readonly record struct PlacedPiece(byte Square, byte Piece);
