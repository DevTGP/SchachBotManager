using Sbm.Native;

namespace Sbm;

/// <summary>Generating, checking, making and taking back moves; SAN.</summary>
public sealed partial class Board
{
    private const int MaxMoves = 256;

    /// <summary>All legal moves of the side to move.</summary>
    public unsafe Move[] LegalMoves()
    {
        var moves = stackalloc ushort[MaxMoves];
        Status.Check(
            Core.sbm_board_legal_moves(_handle, moves, MaxMoves, out var count),
            "Board.LegalMoves"
        );
        return ToMoves(new ReadOnlySpan<ushort>(moves, MaxMoves), count);
    }

    /// <summary>All legal captures of the side to move, en passant and promotions included.</summary>
    public unsafe Move[] LegalCaptures()
    {
        var moves = stackalloc ushort[MaxMoves];
        Status.Check(
            Core.sbm_board_legal_captures(_handle, moves, MaxMoves, out var count),
            "Board.LegalCaptures"
        );
        return ToMoves(new ReadOnlySpan<ushort>(moves, MaxMoves), count);
    }

    /// <summary>
    /// The pseudo-legal moves of the piece on a square, whichever side it belongs to; moves that
    /// leave the own king in check are included (E190).
    /// </summary>
    /// <exception cref="InvalidArgumentException">The square is above 63.</exception>
    public unsafe Move[] AllMovesFrom(byte square)
    {
        var moves = stackalloc ushort[MaxMoves];
        Status.Check(
            Core.sbm_board_all_moves_from(_handle, square, moves, MaxMoves, out var count),
            "Board.AllMovesFrom"
        );
        return ToMoves(new ReadOnlySpan<ushort>(moves, MaxMoves), count);
    }

    /// <summary>
    /// Whether a legal move with the same from-square, to-square and promotion piece exists;
    /// false for <see cref="Move.NullMove"/>, <see cref="Move.Resign"/> and malformed values.
    /// </summary>
    public bool IsLegal(Move move)
    {
        Status.Check(
            Core.sbm_board_is_legal(_handle, move.Value(), out var legal),
            "Board.IsLegal"
        );
        return legal != 0;
    }

    /// <summary>The legal move of this position for a UCI text, with all flags set.</summary>
    /// <exception cref="InvalidUciException">The text is not a move in UCI notation.</exception>
    /// <exception cref="IllegalMoveException">The move is not legal in this position.</exception>
    public Move ParseMove(string uci)
    {
        ArgumentNullException.ThrowIfNull(uci);
        if (Text.HasNul(uci))
        {
            throw Status.Error(Status.InvalidUci, "Board.ParseMove");
        }
        var status = Core.sbm_board_parse_move(_handle, uci, out var value);
        if (status != Status.Ok)
        {
            throw Status.Error(status, $"Board.ParseMove({Text.Quote(uci)})");
        }
        return Move.FromCore(value);
    }

    /// <summary>The legal move in standard algebraic notation, e.g. <c>Nf3</c>.</summary>
    /// <exception cref="IllegalMoveException">The move is not legal in this position.</exception>
    public unsafe string San(Move move)
    {
        var buffer = stackalloc byte[Text.SanBufferSize];
        var status = Core.sbm_board_san(_handle, move.Value(), buffer, Text.SanBufferSize);
        if (status != Status.Ok)
        {
            throw Status.Error(status, $"Board.San({move})");
        }
        return Text.FromC(buffer);
    }

    /// <summary>Makes a legal move and records it in the history.</summary>
    /// <exception cref="IllegalMoveException">The move is not legal in this position.</exception>
    public void MakeMove(Move move)
    {
        var status = Core.sbm_board_make_move(_handle, move.Value());
        if (status != Status.Ok)
        {
            throw Status.Error(status, $"Board.MakeMove({move})");
        }
    }

    /// <summary>Takes back the last move.</summary>
    /// <exception cref="InvalidStateException">
    /// The history is empty or ends with a null move.
    /// </exception>
    public void UndoMove() => Status.Check(Core.sbm_board_undo_move(_handle), "Board.UndoMove");

    /// <summary>Passes the turn without a move, e.g. for null-move pruning.</summary>
    /// <exception cref="InvalidStateException">The side to move is in check.</exception>
    public void MakeNullMove() =>
        Status.Check(Core.sbm_board_make_null_move(_handle), "Board.MakeNullMove");

    /// <summary>Takes back the last null move.</summary>
    /// <exception cref="InvalidStateException">The history does not end with a null move.</exception>
    public void UndoNullMove() =>
        Status.Check(Core.sbm_board_undo_null_move(_handle), "Board.UndoNullMove");
}
