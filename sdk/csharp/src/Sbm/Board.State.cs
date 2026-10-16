using Sbm.Native;

namespace Sbm;

/// <summary>End conditions. Time, resignation and move limits are known only to the referee.</summary>
public sealed partial class Board
{
    /// <summary>Whether the side to move is in check.</summary>
    public bool IsCheck() => Flag(Core.sbm_board_is_check(_handle, out var r), r, "Board.IsCheck");

    /// <summary>Whether the side to move is in check and has no legal move.</summary>
    public bool IsCheckmate() =>
        Flag(Core.sbm_board_is_checkmate(_handle, out var r), r, "Board.IsCheckmate");

    /// <summary>Whether the side to move is not in check and has no legal move.</summary>
    public bool IsStalemate() =>
        Flag(Core.sbm_board_is_stalemate(_handle, out var r), r, "Board.IsStalemate");

    /// <summary>
    /// Whether the position has occurred at least <paramref name="count"/> times, itself included.
    /// </summary>
    /// <exception cref="InvalidArgumentException">The count is below 1.</exception>
    public bool IsRepetition(int count) =>
        Flag(Core.sbm_board_is_repetition(_handle, count, out var r), r, "Board.IsRepetition");

    /// <summary>Whether the halfmove clock is at least 100 and the position is not checkmate.</summary>
    public bool IsFiftyMoveRule() =>
        Flag(Core.sbm_board_is_fifty_move_rule(_handle, out var r), r, "Board.IsFiftyMoveRule");

    /// <summary>Whether neither color can checkmate.</summary>
    public bool IsInsufficientMaterial() =>
        Flag(
            Core.sbm_board_is_insufficient_material(_handle, out var r),
            r,
            "Board.IsInsufficientMaterial"
        );

    /// <summary>Whether that color cannot checkmate.</summary>
    /// <exception cref="InvalidArgumentException">The color is out of range.</exception>
    public bool HasInsufficientMaterial(byte color) =>
        Flag(
            Core.sbm_board_has_insufficient_material(_handle, color, out var r),
            r,
            "Board.HasInsufficientMaterial"
        );

    /// <summary>Stalemate, threefold repetition, fifty-move rule or insufficient material.</summary>
    public bool IsDraw() => Flag(Core.sbm_board_is_draw(_handle, out var r), r, "Board.IsDraw");

    /// <summary>Checkmate or draw.</summary>
    public bool IsGameOver() =>
        Flag(Core.sbm_board_is_game_over(_handle, out var r), r, "Board.IsGameOver");

    private static bool Flag(int status, int result, string what)
    {
        Status.Check(status, what);
        return result != 0;
    }
}
