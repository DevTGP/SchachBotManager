namespace Sbm.Runtime.Referee;

/// <summary>
/// End of a game (bot-protokoll.md, match-runner.md, E44): Result as in PGN, Termination as in
/// game_over, Winner a color or null; Detail explains the ending, e.g. which move was illegal.
/// </summary>
internal sealed record Outcome(string Result, string Termination, byte? Winner, string Detail)
{
    internal const string Draw = "1/2-1/2";
    internal const string NoResult = "*";

    private static readonly string[] Wins = ["1-0", "0-1"];
    private static readonly string[] ColorNames = ["White", "Black"];

    internal static Outcome Win(byte winner, string termination, string detail) =>
        new(Wins[winner], termination, winner, detail);

    internal static Outcome Loss(byte loser, string termination, string detail) =>
        Win(Other(loser), termination, $"{ColorNames[loser]}: {detail}");

    internal static Outcome Drawn(string termination, string detail) =>
        new(Draw, termination, null, detail);

    /// <summary>
    /// The ending the referee scores by itself in this position, if any. The rules come from the
    /// core; repetition and the fifty-move rule end the game at once, without a claim. plies
    /// counts the half-moves played since the start position.
    /// </summary>
    internal static Outcome? OfPosition(Board board, long maxMoves, int plies)
    {
        if (board.IsCheckmate())
        {
            return Win(Other(board.SideToMove()), "checkmate", "checkmate");
        }
        if (board.IsStalemate())
        {
            return Drawn("stalemate", "stalemate");
        }
        if (board.IsInsufficientMaterial())
        {
            return Drawn("insufficient_material", "neither side can checkmate");
        }
        if (board.IsFiftyMoveRule())
        {
            return Drawn("fifty_move_rule", "50 moves without capture or pawn move");
        }
        if (board.IsRepetition(3))
        {
            return Drawn("threefold_repetition", "the position occurred three times");
        }
        return plies >= 2 * maxMoves
            ? Drawn("max_moves", $"move limit of {maxMoves} moves reached")
            : null;
    }

    /// <summary>Loss on time, or a draw if the opponent cannot checkmate with its material.</summary>
    internal static Outcome OfTimeout(Board board, byte loser)
    {
        var winner = Other(loser);
        return board.HasInsufficientMaterial(winner)
            ? Drawn(
                "timeout_insufficient_material",
                $"{ColorNames[loser]} ran out of time, {ColorNames[winner]} cannot checkmate"
            )
            : Loss(loser, "timeout", "ran out of time");
    }

    /// <summary>The ending if bots failed to start; both failing aborts without a winner.</summary>
    internal static Outcome? OfStartup(Outcome? white, Outcome? black) =>
        (white, black) switch
        {
            ({ } first, { } second) => new(
                NoResult,
                "startup_timeout",
                null,
                $"neither bot started: {first.Detail}; {second.Detail}"
            ),
            _ => white ?? black,
        };

    private static byte Other(byte color) => (byte)(1 - color);
}
