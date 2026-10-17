using Sbm.Runtime.Referee;

namespace Sbm.Runtime.Play;

/// <summary>The opponent of a local game of Sdk.Play; Name is shown in the game.</summary>
internal abstract record Opponent(string Name)
{
    /// <summary>A new player for one game; the match starts and closes it.</summary>
    internal abstract Player CreatePlayer();
}

/// <summary>
/// A reference bot of the SDK (E68): it plays in a thread of the program with its log hidden, so
/// it needs neither Python nor a second program.
/// </summary>
internal sealed record ReferenceOpponent(string Name, Func<Bot> Create, string ClassName)
    : Opponent(Name)
{
    internal override Player CreatePlayer() =>
        new ThreadPlayer(Name, Create, ClassName, muted: true);
}

/// <summary>A bot as its own process: a bot file or a command; its log is dropped.</summary>
internal sealed record ProcessOpponent(string Name, string Program, IReadOnlyList<string> Arguments)
    : Opponent(Name)
{
    internal override Player CreatePlayer() => new ProcessPlayer(Name, Program, Arguments);
}
