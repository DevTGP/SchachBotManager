// An uploaded C# bot as the verification sees it: two source files and a data file (E203, E204).
using System.Text;
using Sbm;

namespace Uploaded;

public sealed class UploadedBot : Bot
{
    private readonly string[] _book = Encoding
        .UTF8.GetString(Sdk.LoadData("book.txt"))
        .Split('\n', StringSplitOptions.RemoveEmptyEntries | StringSplitOptions.TrimEntries);

    public override Move ChooseMove(Board board, Clock clock) => Opening.FirstMove(board, _book);
}
