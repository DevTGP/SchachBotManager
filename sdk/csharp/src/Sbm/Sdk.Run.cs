using Sbm.Runtime;

namespace Sbm;

public static partial class Sdk
{
    /// <summary>
    /// Entry point and the only call in the bot's Main: creates one instance of TBot, plays one
    /// game with it and returns when the game is over. Transport and log level come from the
    /// command line or environment (E61): --tcp [PORT], --log-level LEVEL, --log-file PATH or
    /// SBM_TRANSPORT, SBM_PORT, SBM_LOG_LEVEL, SBM_LOG_FILE. An exception from the bot is logged
    /// at ERROR and ends the process with exit code 1 (E49).
    /// </summary>
    /// <typeparam name="TBot">The bot class.</typeparam>
    /// <param name="viewer">
    /// true would open the viewer window (E106); this SDK has no viewer program yet and says so
    /// once at WARN.
    /// </param>
    public static void Run<TBot>(bool viewer = false)
        where TBot : Bot, new()
    {
        var code = Runner.Run(
            () => new TBot(),
            typeof(TBot).Name,
            viewer,
            Environment.GetCommandLineArgs()[1..],
            Environment.GetEnvironmentVariable
        );
        if (code != 0)
        {
            Environment.Exit(code);
        }
    }
}
