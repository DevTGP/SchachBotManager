using System.Globalization;
using System.Net.Sockets;
using System.Net.WebSockets;
using Sbm.Runtime.Referee;
using Sbm.Runtime.Remote;
using Sbm.Runtime.Viewer;

namespace Sbm.Runtime.Play;

/// <summary>
/// Sdk.Play without the process: checks all arguments, plays the games, logs each result and
/// the score (spec/api/runtime.json, E120).
/// </summary>
internal static class Starter
{
    internal const string TokenVariable = "SBM_TOKEN";

    private static readonly string[] Colors = ["white", "black", "random"];
    private static readonly string[] ColorNames = ["white", "black"];

    /// <summary>
    /// The games in order and the exit code: 1 after an error of the bot, the protocol, the
    /// server or the connection, which ends the series. Wrong arguments throw
    /// InvalidArgumentException before the first game. open and sleep reach RemoteGame.
    /// </summary>
    internal static (IReadOnlyList<PlayedGame> Games, int Code) Play(
        Func<Bot> create,
        string botName,
        PlayRequest request,
        Func<string, string?> env,
        Func<RemoteOptions, (Seat, IChannel)>? open = null,
        Action<TimeSpan>? sleep = null
    )
    {
        var color = Check(request);
        Func<byte, int, PlayedGame> round = string.IsNullOrEmpty(request.Server)
            ? Local(create, botName, request)
            : Remote(create, botName, request, env, open, sleep);
        var first =
            color == "random" ? (byte)Random.Shared.Next(2) : (byte)Array.IndexOf(Colors, color);
        var window = request.Viewer ? ViewerWindow.Open(env) : null;
        var played = new List<PlayedGame>();
        try
        {
            for (var number = 1; number <= request.Games; number++)
            {
                var own = number % 2 == 1 ? first : (byte)(1 - first);
                played.Add(round(own, number));
                Report(played[^1], number, request.Games);
            }
        }
        catch (BotFailureException error)
        {
            Log.Error(Guard.Describe(error));
            return (played, 1);
        }
        catch (ProtocolException error)
        {
            Log.Error($"protocol error: {error.Message}");
            return (played, 1);
        }
        catch (Exception error)
            when (error is RemoteException or IOException or SocketException or WebSocketException)
        {
            Log.Error($"play stopped: {error.Message}");
            return (played, 1);
        }
        finally
        {
            window?.WaitUntilClosed();
        }
        ReportScore(played);
        return (played, 0);
    }

    /// <summary>Common checks; returns the color in lower case.</summary>
    private static string Check(PlayRequest request)
    {
        if (string.IsNullOrWhiteSpace(request.Opponent))
        {
            throw new InvalidArgumentException("play: opponent must be a non-empty string");
        }
        var color = request.Color?.ToLowerInvariant();
        if (color is null || !Colors.Contains(color))
        {
            throw new InvalidArgumentException(
                $"play: color must be one of {string.Join(", ", Colors)}"
            );
        }
        if (request.Games < 1)
        {
            throw new InvalidArgumentException(
                $"play: games must be an int of at least 1, not {request.Games}"
            );
        }
        return color;
    }

    private static (long InitialMs, long IncrementMs) TimeControlOf(string? time)
    {
        try
        {
            return TimeControl.Parse(string.IsNullOrEmpty(time) ? RemoteOptions.DefaultTime : time);
        }
        catch (FormatException error)
        {
            throw new InvalidArgumentException($"play: {error.Message}");
        }
    }

    private static Func<byte, int, PlayedGame> Local(
        Func<Bot> create,
        string botName,
        PlayRequest request
    )
    {
        if (!string.IsNullOrEmpty(request.Discipline))
        {
            throw new InvalidArgumentException(
                "play: a discipline needs a server; locally use time"
            );
        }
        var (initialMs, incrementMs) = TimeControlOf(request.Time);
        if (OpponentParser.IsTcp(request.Opponent))
        {
            throw new InvalidArgumentException(
                "play: a TCP opponent is not possible; use sbm-arena"
            );
        }
        Opponent opponent;
        try
        {
            opponent = OpponentParser.Parse(request.Opponent);
        }
        catch (OpponentException error)
        {
            throw new InvalidArgumentException($"play: opponent: {error.Message}");
        }
        var names = OpponentParser.UniqueNames([OpponentParser.Shorten(botName), opponent.Name]);
        opponent = opponent with { Name = names[1] };
        var settings = new MatchSettings(initialMs, incrementMs);
        return (color, number) =>
            LocalGame.Play(create, botName, names[0], opponent, color, settings, number);
    }

    private static Func<byte, int, PlayedGame> Remote(
        Func<Bot> create,
        string botName,
        PlayRequest request,
        Func<string, string?> env,
        Func<RemoteOptions, (Seat, IChannel)>? open,
        Action<TimeSpan>? sleep
    )
    {
        var server = request.Server!;
        if (
            !Uri.TryCreate(server, UriKind.Absolute, out var uri)
            || uri.Scheme is not ("http" or "https")
            || uri.Authority.Length == 0
        )
        {
            throw new InvalidArgumentException(
                $"play: server must be an http or https address: {PyText.Repr(server)}"
            );
        }
        var token = string.IsNullOrEmpty(request.Token) ? env(TokenVariable) : request.Token;
        if (string.IsNullOrEmpty(token))
        {
            throw new InvalidArgumentException(
                $"play: a server needs a token, or {TokenVariable} set"
            );
        }
        var discipline = string.IsNullOrEmpty(request.Discipline) ? null : request.Discipline;
        var time = string.IsNullOrEmpty(request.Time) ? null : request.Time;
        if (discipline is not null && time is not null)
        {
            throw new InvalidArgumentException(
                "play: give either a discipline or a time, not both"
            );
        }
        if (discipline is null)
        {
            TimeControlOf(time);
        }
        return (color, _) =>
        {
            var remote = new RemoteOptions(server, token, request.Opponent)
            {
                Color = ColorNames[color],
                Discipline = discipline,
                Time = time ?? RemoteOptions.DefaultTime,
            };
            return RemoteGame.Play(create, botName, remote, open, sleep);
        };
    }

    private static void Report(PlayedGame game, int number, int games)
    {
        Log.SetPly(null);
        Log.Info(
            $"game {number}/{games} ({game.GameId}) as {ColorNames[game.Color]} "
                + $"against {game.OpponentName}: {game.Result} {game.Termination}"
        );
    }

    private static double? Points(PlayedGame game) =>
        game.Result switch
        {
            Outcome.Draw => 0.5,
            "1-0" => game.Color == Color.White ? 1.0 : 0.0,
            "0-1" => game.Color == Color.Black ? 1.0 : 0.0,
            _ => null,
        };

    private static void ReportScore(List<PlayedGame> played)
    {
        var points = played.Select(Points).ToList();
        var scored = points.OfType<double>().ToList();
        var sum = scored.Sum().ToString(CultureInfo.InvariantCulture);
        Log.Info(
            $"score {sum}/{scored.Count}: {scored.Count(value => value == 1.0)} won, "
                + $"{scored.Count(value => value == 0.5)} drawn, "
                + $"{scored.Count(value => value == 0.0)} lost, "
                + $"{points.Count(value => value is null)} without result"
        );
    }
}
