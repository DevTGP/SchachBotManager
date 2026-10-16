// Reads a file through System.IO, which the rules do not allow; the analysis must find it (E203).
using Sbm;

namespace Forbidden;

public sealed class ForbiddenBot : Bot
{
    public override Move ChooseMove(Board board, Clock clock)
    {
        System.IO.File.ReadAllText("/etc/passwd");
        return board.LegalMoves()[0];
    }
}
