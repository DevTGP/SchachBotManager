namespace Sbm.Bots;

/// <summary>
/// Plays a random legal move: the weakest possible opponent of Sdk.Play. Port of
/// sbm.bots.random_mover in the Python SDK.
/// </summary>
internal sealed class RandomBot : Bot
{
    private readonly Random _random = new();

    public override Move ChooseMove(Board board, Clock clock)
    {
        var moves = board.LegalMoves();
        return moves[_random.Next(moves.Length)];
    }
}
