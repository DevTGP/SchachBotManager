namespace Sbm.Tests.Runtime;

/// <summary>Plays the first legal move and records what the SDK passes in.</summary>
internal class FirstMoveBot : Bot
{
    public List<GameInfo> Starts { get; } = [];

    public List<(string Fen, Clock Clock)> Turns { get; } = [];

    public List<GameResult> Ends { get; } = [];

    public override void OnGameStart(GameInfo info) => Starts.Add(info);

    public override Move ChooseMove(Board board, Clock clock)
    {
        Turns.Add((board.Fen(), clock));
        return board.LegalMoves()[0];
    }

    public override void OnGameEnd(GameResult result) => Ends.Add(result);
}
