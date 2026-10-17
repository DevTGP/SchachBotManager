using System.Net.Sockets;
using System.Net.WebSockets;
using System.Text;
using Sbm.Runtime.Remote;
using Sbm.Runtime.Viewer;

namespace Sbm.Runtime;

/// <summary>Sdk.Run without the process: options, log, transport and one game (spec/api/runtime.json).</summary>
internal static class Runner
{
    /// <summary>The exit code: 0 after a game, 1 after an error of the bot, the protocol or the options.</summary>
    internal static int Run(
        Func<Bot> create,
        string botName,
        bool viewer,
        IReadOnlyList<string> args,
        Func<string, string?> env,
        Func<Options, IChannel>? open = null
    )
    {
        Options options;
        try
        {
            options = OptionsParser.Parse(args, env);
        }
        catch (OptionsException error)
        {
            Console.Error.WriteLine($"sbm: {error.Message}");
            return 1;
        }
        StreamWriter? file = null;
        if (options.LogFile is not null)
        {
            try
            {
                file = new StreamWriter(options.LogFile, append: true, new UTF8Encoding(false));
            }
            catch (Exception error)
                when (error is IOException or UnauthorizedAccessException or ArgumentException)
            {
                Console.Error.WriteLine($"sbm: cannot open the log file: {error.Message}");
                return 1;
            }
        }
        Log.Configure(options.LogLevel, file);
        var window = viewer ? ViewerWindow.Open(env) : null;
        try
        {
            return Play(create, botName, options, open ?? Open);
        }
        finally
        {
            window?.WaitUntilClosed();
            Log.Configure(Log.Level(), null);
            file?.Dispose();
        }
    }

    private static int Play(
        Func<Bot> create,
        string botName,
        Options options,
        Func<Options, IChannel> open
    )
    {
        IChannel channel;
        try
        {
            channel = open(options);
        }
        catch (RemoteException error)
        {
            Log.Error(error.Message);
            return 1;
        }
        catch (Exception error) when (error is IOException or SocketException or WebSocketException)
        {
            var where = options.Remote?.Url ?? $"the arena on 127.0.0.1:{options.Port}";
            Log.Error($"cannot connect to {where}: {error.Message}");
            return 1;
        }
        catch (ProtocolException error)
        {
            Log.Error($"protocol error: {error.Message}");
            return 1;
        }
        using (channel)
        {
            try
            {
                new Game(Guard.Call($"{botName}()", create), channel).Play();
                return 0;
            }
            catch (BotFailureException error)
            {
                Log.Error(Guard.Describe(error));
                return 1;
            }
            catch (ProtocolException error)
            {
                Log.Error($"protocol error: {error.Message}");
                return 1;
            }
        }
    }

    private static IChannel Open(Options options) =>
        options.Transport switch
        {
            Transport.Remote => RemoteOpening.Open(options.Remote!).Channel,
            Transport.Tcp => Transports.OpenTcp(options.Port),
            _ => Transports.OpenStdio(),
        };
}
