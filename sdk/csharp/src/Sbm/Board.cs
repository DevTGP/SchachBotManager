using Sbm.Native;

namespace Sbm;

/// <summary>
/// Chess position with move history, backed by the shared core. The native handle is freed by
/// the garbage collector; a board needs no disposing (kern-c-schnittstelle.md).
/// </summary>
public sealed partial class Board
{
    private readonly BoardHandle _handle;

    /// <summary>The starting position.</summary>
    public Board()
    {
        Status.Check(Core.sbm_board_new(out var handle), "Board");
        _handle = handle;
    }

    private Board(BoardHandle handle)
    {
        _handle = handle;
    }

    /// <summary>The position of a FEN; the move history is empty.</summary>
    /// <exception cref="InvalidFenException">The text is not a valid FEN.</exception>
    public static Board FromFen(string fen)
    {
        ArgumentNullException.ThrowIfNull(fen);
        if (Text.HasNul(fen))
        {
            throw Status.Error(Status.InvalidFen, "Board.FromFen");
        }
        Status.Check(Core.sbm_board_from_fen(fen, out var handle), "Board.FromFen");
        return new Board(handle);
    }

    /// <summary>An independent copy, move history included.</summary>
    public Board Copy()
    {
        Status.Check(Core.sbm_board_copy(_handle, out var handle), "Board.Copy");
        return new Board(handle);
    }

    /// <summary>The position as FEN.</summary>
    public unsafe string Fen()
    {
        var buffer = stackalloc byte[Text.FenBufferSize];
        Status.Check(Core.sbm_board_fen(_handle, buffer, Text.FenBufferSize), "Board.Fen");
        return Text.FromC(buffer);
    }

    /// <summary>Zobrist hash with the Polyglot keys, equal to the Polyglot book key.</summary>
    public ulong Hash()
    {
        Status.Check(Core.sbm_board_hash(_handle, out var hash), "Board.Hash");
        return hash;
    }

    /// <summary>All moves made since the starting position, oldest first.</summary>
    public unsafe Move[] MoveHistory()
    {
        const string what = "Board.MoveHistory";
        var status = Core.sbm_board_move_history(_handle, null, 0, out var count);
        if (count == 0)
        {
            Status.Check(status, what);
            return [];
        }
        var moves = new ushort[count];
        fixed (ushort* pointer = moves)
        {
            Status.Check(Core.sbm_board_move_history(_handle, pointer, count, out count), what);
        }
        return ToMoves(moves, count);
    }

    /// <summary>The position as text diagram for logs.</summary>
    public unsafe string ToText()
    {
        var buffer = stackalloc byte[Text.TextBufferSize];
        Status.Check(Core.sbm_board_to_text(_handle, buffer, Text.TextBufferSize), "Board.ToText");
        return Text.FromC(buffer);
    }

    /// <summary>The position for the debugger, e.g. <c>Board.FromFen("…")</c>.</summary>
    public override string ToString() => $"Board.FromFen({Text.Quote(Fen())})";

    private static Move[] ToMoves(ReadOnlySpan<ushort> values, uint count)
    {
        var moves = new Move[count];
        for (var i = 0; i < moves.Length; i++)
        {
            moves[i] = Move.FromCore(values[i]);
        }
        return moves;
    }
}
