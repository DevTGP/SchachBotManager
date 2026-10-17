using System.Text.Json;

namespace Sbm.Runtime.Referee;

/// <summary>
/// One game from init to game_over between two players (match-runner.md, bot-protokoll.md),
/// ported from the referee of the Python SDK. The match owns the authoritative board, the clock
/// and the result; everything the players send is checked strictly before it counts. now
/// returns monotonic nanoseconds and is replaceable for tests.
/// </summary>
internal sealed class Match
{
    private readonly Player[] _players;
    private readonly MatchSettings _settings;
    private readonly Func<long> _now;
    private readonly Board _board;
    private readonly GameClock _clock;
    private readonly List<string> _moves = [];

    // Sides that get no game_over: gone, or stopped hard after running out of time.
    private readonly HashSet<byte> _silent = [];
    private bool _played;

    /// <summary>Throws InvalidArgumentException for a name outside 1 to 64 characters.</summary>
    internal Match(Player white, Player black, MatchSettings settings, Func<long>? now = null)
    {
        MatchSettings.CheckName("white name", white.Name);
        MatchSettings.CheckName("black name", black.Name);
        _players = [white, black];
        _settings = settings;
        _now = now ?? Monotonic.Now;
        _board = Board.FromFen(settings.StartFen);
        _clock = new GameClock(settings);
    }

    /// <summary>The accepted moves in UCI notation.</summary>
    internal IReadOnlyList<string> Moves => _moves;

    /// <summary>
    /// Runs the game to its end; may be called once. Exceptions other than the player ones are
    /// infrastructure errors: they propagate after both players are closed.
    /// </summary>
    internal Outcome Play()
    {
        if (_played)
        {
            throw new InvalidOperationException("a match can be played only once");
        }
        _played = true;
        try
        {
            var outcome = StartSides() ?? PositionOutcome();
            while (outcome is null)
            {
                outcome = Turn();
            }
            Announce(outcome);
            return outcome;
        }
        finally
        {
            Close();
        }
    }

    /// <summary>Starts white, then black, so only one bot uses the processor at a time.</summary>
    private Outcome? StartSides()
    {
        var white = StartSide(Color.White);
        var black = StartSide(Color.Black);
        return Outcome.OfStartup(white, black);
    }

    private Outcome? StartSide(byte color)
    {
        var player = _players[color];
        var startupMs = _settings.StartupMs;
        var start = _now();
        long? deadline = _clock.Running ? start + startupMs * GameClock.NanosecondsPerMs : null;
        byte[] line;
        try
        {
            player.Start();
            player.Send(RefereeMessages.Init(_settings, color, _players[1 - color].Name));
            line = player.Receive(deadline);
        }
        catch (PlayerTimeoutException)
        {
            return StartupTimeout(color);
        }
        catch (PlayerClosedException error)
        {
            return Gone(color, error);
        }
        catch (LineTooLongException)
        {
            player.Suspend();
            return Violation(color, LineTooLong());
        }
        if (_clock.Running && GameClock.ElapsedMs(start, _now()) > startupMs)
        {
            return StartupTimeout(color);
        }
        player.Suspend();
        BotMessage message;
        try
        {
            message = BotMessages.Read(line);
        }
        catch (ViolationException violation)
        {
            return Violation(color, violation);
        }
        return message is ReadyMessage
            ? null
            : Violation(
                color,
                new ViolationException("unexpected_message", "the first message must be ready")
            );
    }

    private Outcome StartupTimeout(byte color)
    {
        // Frozen at once, so it cannot take the processor from the other side's startup.
        _players[color].Suspend();
        _silent.Add(color);
        return Outcome.Loss(color, "startup_timeout", $"no ready within {_settings.StartupMs} ms");
    }

    private Outcome? Turn()
    {
        var color = _board.SideToMove();
        var player = _players[color];
        byte[] line;
        long spent;
        try
        {
            player.Resume();
            if (RejectWaitingLine(color) is { } early)
            {
                return early;
            }
            player.Send(TurnMessage(color));
            var start = _now();
            line = player.Receive(_clock.DeadlineNs(color, start));
            spent = GameClock.ElapsedMs(start, _now());
        }
        catch (PlayerTimeoutException)
        {
            return Timeout(color);
        }
        catch (PlayerClosedException error)
        {
            return Gone(color, error);
        }
        catch (LineTooLongException)
        {
            player.Suspend();
            return Violation(color, LineTooLong());
        }
        if (_clock.IsOver(color, spent))
        {
            return Timeout(color);
        }
        player.Suspend();
        BotMessage message;
        try
        {
            message = BotMessages.Read(line);
        }
        catch (ViolationException violation)
        {
            return Violation(color, violation);
        }
        return message switch
        {
            ResignMessage => Outcome.Loss(color, "resignation", "resigned"),
            MoveMessage move => MakeMove(color, move.Uci, spent),
            _ => Violation(
                color,
                new ViolationException("unexpected_message", "expected move or resign")
            ),
        };
    }

    /// <summary>A line sent outside the own turn breaks the protocol (only possible over tcp).</summary>
    private Outcome? RejectWaitingLine(byte color)
    {
        try
        {
            _players[color].Receive(_now());
        }
        catch (PlayerTimeoutException)
        {
            return null;
        }
        catch (LineTooLongException) { }
        _players[color].Suspend();
        return Violation(
            color,
            new ViolationException("unexpected_message", "a message arrived before turn")
        );
    }

    private Action<Utf8JsonWriter> TurnMessage(byte color) =>
        RefereeMessages.Turn(
            LastMove(),
            _board.Fen(),
            _moves.Count,
            _clock.RemainingMs(color),
            _clock.RemainingMs((byte)(1 - color))
        );

    private Outcome? MakeMove(byte color, string uci, long spent)
    {
        Move move;
        try
        {
            move = _board.ParseMove(uci);
        }
        catch (ChessException)
        {
            var violation = new ViolationException(
                "illegal_move",
                $"{uci} is not legal in this position"
            );
            return Violation(color, violation, "illegal_move");
        }
        _board.MakeMove(move);
        _clock.Charge(color, spent);
        _moves.Add(uci);
        return PositionOutcome();
    }

    private Outcome? PositionOutcome() =>
        Outcome.OfPosition(_board, _settings.MaxMoves, _moves.Count);

    private Outcome Timeout(byte color)
    {
        _clock.Flag(color);
        _silent.Add(color);
        return Outcome.OfTimeout(_board, color);
    }

    private Outcome Gone(byte color, PlayerClosedException error)
    {
        _silent.Add(color);
        return Outcome.Loss(color, error.Termination, $"left the game: {error.Message}");
    }

    /// <summary>Tells the side what it did wrong; game_over follows at the end.</summary>
    private Outcome Violation(
        byte color,
        ViolationException violation,
        string termination = "protocol_violation"
    )
    {
        Send(color, RefereeMessages.Error(violation.Code, violation.Message));
        return Outcome.Loss(color, termination, $"{violation.Code}: {violation.Message}");
    }

    private void Announce(Outcome outcome)
    {
        var message = RefereeMessages.GameOver(
            outcome.Result,
            outcome.Termination,
            LastMove(),
            _board.Fen(),
            _moves.Count
        );
        foreach (var color in new[] { Color.White, Color.Black })
        {
            if (_silent.Contains(color))
            {
                continue;
            }
            try
            {
                _players[color].Resume();
            }
            catch (PlayerClosedException) { }
            Send(color, message);
        }
    }

    private void Send(byte color, Action<Utf8JsonWriter> message)
    {
        if (_silent.Contains(color))
        {
            return;
        }
        try
        {
            _players[color].Send(message);
        }
        catch (PlayerClosedException)
        {
            _silent.Add(color);
        }
    }

    /// <summary>Closes both players even if one of them fails to close.</summary>
    private void Close()
    {
        try
        {
            _players[Color.White].Dispose();
        }
        finally
        {
            _players[Color.Black].Dispose();
        }
    }

    private string? LastMove() => _moves.Count > 0 ? _moves[^1] : null;

    private static ViolationException LineTooLong() =>
        new("line_too_long", $"a line is longer than {Player.MaxLineBytes} bytes");
}
