using Sbm.Native;

namespace Sbm;

/// <summary>
/// A move as 16-bit value: bits 0 to 5 from-square, 6 to 11 to-square, 12 to 15 flags (E34).
/// Two moves are equal if their values are equal. The bit operations are computed here; only
/// <see cref="Parse"/> and <see cref="Uci"/> call the core (kern-c-schnittstelle.md).
/// </summary>
public readonly struct Move : IEquatable<Move>
{
    private const int ToShift = 6;
    private const int FlagShift = 12;

    /// <summary>No move; also the move recorded for <see cref="Board.MakeNullMove"/>.</summary>
    public static readonly Move NullMove = new(0);

    /// <summary>Returned from ChooseMove to resign; never a legal move.</summary>
    public static readonly Move Resign = new(0xFFFF);

    private readonly ushort _value;

    /// <summary>A move from its squares and flags.</summary>
    /// <exception cref="InvalidArgumentException">
    /// A square is above 63, or the flags are above 15 or one of the unused values 6 and 7.
    /// </exception>
    public Move(byte fromSquare, byte toSquare, byte flags)
    {
        if (fromSquare > 63 || toSquare > 63)
        {
            throw new InvalidArgumentException("Move: squares must be 0 to 63");
        }
        if (flags > 15 || IsUnused(flags))
        {
            throw new InvalidArgumentException("Move: flags must be 0 to 5 or 8 to 15");
        }
        _value = (ushort)(fromSquare | (toSquare << ToShift) | (flags << FlagShift));
    }

    private Move(ushort value)
    {
        _value = value;
    }

    /// <summary>The move with this 16-bit value; NULL_MOVE and RESIGN included.</summary>
    /// <exception cref="InvalidArgumentException">The flags are 6 or 7.</exception>
    public static Move FromValue(ushort value)
    {
        if (IsUnused(FlagsOf(value)))
        {
            throw new InvalidArgumentException("Move.FromValue: flags 6 and 7 are unused");
        }
        return new Move(value);
    }

    /// <summary>
    /// A move from UCI text without a position, e.g. <c>e7e8q</c>. Without a board the flags
    /// are only those for a promotion; <see cref="Board.ParseMove"/> sets all of them.
    /// </summary>
    /// <exception cref="InvalidUciException">The text is not a move in UCI notation.</exception>
    public static Move Parse(string uci)
    {
        ArgumentNullException.ThrowIfNull(uci);
        if (Text.HasNul(uci))
        {
            throw Status.Error(Status.InvalidUci, "Move.Parse");
        }
        Status.Check(Core.sbm_move_parse(uci, out var value), "Move.Parse");
        return new Move(value);
    }

    /// <summary>The 16-bit value of the move.</summary>
    public ushort Value() => _value;

    /// <summary>The square the piece moves from.</summary>
    public byte FromSquare() => (byte)(_value & 0x3F);

    /// <summary>The square the piece moves to.</summary>
    public byte ToSquare() => (byte)((_value >> ToShift) & 0x3F);

    /// <summary>The flags of the move, one of <see cref="MoveFlags"/>.</summary>
    public byte Flags() => FlagsOf(_value);

    /// <summary>The piece type promoted to, or <see cref="PieceType.NoPieceType"/>.</summary>
    public byte Promotion()
    {
        var flags = Flags();
        return flags >= MoveFlags.PromotionKnight ? (byte)((flags & 3) + 1) : PieceType.NoPieceType;
    }

    /// <summary>Whether the move promotes a pawn.</summary>
    public bool IsPromotion() => Flags() >= MoveFlags.PromotionKnight;

    /// <summary>Whether the move captures, en passant and promotions included.</summary>
    public bool IsCapture()
    {
        var flags = Flags();
        return flags == MoveFlags.Capture
            || flags == MoveFlags.EnPassant
            || flags >= MoveFlags.PromotionCaptureKnight;
    }

    /// <summary>Whether the move castles.</summary>
    public bool IsCastling()
    {
        var flags = Flags();
        return flags == MoveFlags.KingCastle || flags == MoveFlags.QueenCastle;
    }

    /// <summary>Whether the move captures en passant.</summary>
    public bool IsEnPassant() => Flags() == MoveFlags.EnPassant;

    /// <summary>The move in UCI notation, e.g. <c>e2e4</c> or <c>e7e8q</c>.</summary>
    /// <exception cref="InvalidArgumentException">
    /// The move is <see cref="NullMove"/> or <see cref="Resign"/>.
    /// </exception>
    public unsafe string Uci()
    {
        var buffer = stackalloc byte[Text.UciBufferSize];
        Status.Check(Core.sbm_move_uci(_value, buffer, Text.UciBufferSize), "Move.Uci");
        return Text.FromC(buffer);
    }

    /// <inheritdoc/>
    public bool Equals(Move other) => _value == other._value;

    /// <inheritdoc/>
    public override bool Equals(object? obj) => obj is Move other && Equals(other);

    /// <inheritdoc/>
    public override int GetHashCode() => _value;

    /// <summary>The move for logs and the debugger, e.g. <c>&lt;Move e2e4 flags=1&gt;</c>.</summary>
    public override unsafe string ToString()
    {
        if (_value == NullMove._value)
        {
            return "<Move NullMove>";
        }
        if (_value == Resign._value)
        {
            return "<Move Resign>";
        }
        var buffer = stackalloc byte[Text.UciBufferSize];
        if (Core.sbm_move_uci(_value, buffer, Text.UciBufferSize) != Status.Ok)
        {
            return $"<Move {_value}>";
        }
        return $"<Move {Text.FromC(buffer)} flags={Flags()}>";
    }

    /// <summary>Whether both moves have the same value.</summary>
    public static bool operator ==(Move left, Move right) => left.Equals(right);

    /// <summary>Whether the moves have different values.</summary>
    public static bool operator !=(Move left, Move right) => !left.Equals(right);

    internal static Move FromCore(ushort value) => new(value);

    private static byte FlagsOf(ushort value) => (byte)(value >> FlagShift);

    private static bool IsUnused(byte flags) => flags is 6 or 7;
}
