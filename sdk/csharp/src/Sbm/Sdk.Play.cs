using Sbm.Runtime.Play;

namespace Sbm;

public static partial class Sdk
{
    /// <summary>
    /// Plays games of TBot against opponent from code, so a starter program needs neither
    /// arguments nor environment variables (E120). Without server the games run locally: the
    /// referee in this program, the own bot in a thread of it, so a debugger stops at its
    /// breakpoints. With server each game is asked for at the web API and played over WebSocket
    /// as with --remote of Run (E116). Each result is logged at INFO, the score after the last
    /// game. An exception of the bot, a refused game or a lost connection is logged at ERROR and
    /// ends the process with exit code 1, as with Run.
    /// </summary>
    /// <typeparam name="TBot">The own bot class.</typeparam>
    /// <param name="opponent">
    /// Without server: a reference bot (random, material), a bot file (.py, .dll or a program) or
    /// a command as in the local arena (E67). With server: the name of a checked bot on the
    /// server.
    /// </param>
    /// <param name="server">
    /// Address of the site, e.g. https://schachbotmanager.example.org; null or empty plays
    /// locally.
    /// </param>
    /// <param name="token">
    /// API token of a coder, needed with server; null or empty takes SBM_TOKEN from the
    /// environment.
    /// </param>
    /// <param name="color">
    /// Own color in the first game: white, black or random; later games alternate.
    /// </param>
    /// <param name="time">
    /// Time control SECONDS+INCREMENT, default 60+1; not together with discipline.
    /// </param>
    /// <param name="discipline">With server only: a discipline by name instead of time.</param>
    /// <param name="games">Number of games, at least 1.</param>
    /// <param name="viewer">
    /// true opens one viewer window for all games, as with Run (E108); after the last game the
    /// program waits until it is closed.
    /// </param>
    /// <returns>One entry per game in the order played.</returns>
    /// <exception cref="InvalidArgumentException">An argument is outside its range.</exception>
    public static IReadOnlyList<PlayedGame> Play<TBot>(
        string opponent,
        string? server = null,
        string? token = null,
        string color = "random",
        string? time = null,
        string? discipline = null,
        int games = 1,
        bool viewer = false
    )
        where TBot : Bot, new()
    {
        var request = new PlayRequest(opponent)
        {
            Server = server,
            Token = token,
            Color = color,
            Time = time,
            Discipline = discipline,
            Games = games,
            Viewer = viewer,
        };
        var (played, code) = Starter.Play(
            () => new TBot(),
            typeof(TBot).Name,
            request,
            Environment.GetEnvironmentVariable
        );
        if (code != 0)
        {
            Environment.Exit(code);
        }
        return played;
    }
}
