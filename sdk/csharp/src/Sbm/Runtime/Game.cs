using System.Text.Json;
using Sbm.Runtime.Viewer;

namespace Sbm.Runtime;

/// <summary>One game from the bot's side: init, turns and game_over (state machine of bot-protokoll.md).</summary>
internal sealed class Game(Bot bot, Channel channel)
{
    private Board? _board;
    private long _incrementMs;

    /// <summary>Set once init arrives.</summary>
    internal GameInfo? Info { get; private set; }

    /// <summary>Set once game_over arrives.</summary>
    internal GameResult? Result { get; private set; }

    /// <summary>Answers referee messages until game_over or the end of the input.</summary>
    internal void Play()
    {
        while (channel.Receive() is { } message)
        {
            var kind = message.TryGetProperty("type", out var type) ? type : default;
            switch (kind.ValueKind == JsonValueKind.String ? kind.GetString() : null)
            {
                case "init":
                    Start(message);
                    break;
                case "turn":
                    Turn(message);
                    break;
                case "error":
                    Log.Error(
                        $"referee reports {Text(message, "code")}: {Text(message, "message")}"
                    );
                    break;
                case "game_over":
                    End(message);
                    return;
                default:
                    Log.Warn(
                        $"ignoring a message of unknown type {Protocol.Json(message, "type")}"
                    );
                    break;
            }
        }
        Log.Warn("input ended before game_over");
    }

    private void Start(JsonElement init)
    {
        if (_board is not null)
        {
            throw new ProtocolException("init: second init in one game");
        }
        var info = Protocol.GameInfo(init);
        Info = info;
        try
        {
            _board = Board.FromFen(info.StartFen);
        }
        catch (ChessException error)
        {
            throw new ProtocolException($"init: {error.Message}");
        }
        _incrementMs = info.IncrementMs;
        var supported = Protocol.Supported(init);
        if (!supported.Any(Protocol.IsThisVersion))
        {
            // The referee diagnoses the mismatch after ready; this line tells the author why.
            var versions = string.Join(", ", supported.Select(version => version.GetRawText()));
            Log.Error(
                $"the referee supports protocol versions [{versions}], "
                    + $"this SDK speaks version {Protocol.Version}; update the SDK"
            );
        }
        Guard.Call("OnGameStart", () => bot.OnGameStart(info));
        GameView.Started(bot.GetType().Name, info);
        channel.Send(json => Protocol.Ready(json, Sdk.Version));
    }

    private void Turn(JsonElement turn)
    {
        // First, so that ElapsedMs covers everything the SDK does in this turn.
        var clock = new Clock(
            Protocol.Integer(turn, "remaining_ms"),
            Protocol.Integer(turn, "opponent_remaining_ms"),
            _incrementMs
        );
        if (_board is null)
        {
            throw new ProtocolException("turn before init");
        }
        var ply = Protocol.SmallInteger(turn, "ply");
        Log.SetPly(ply);
        var board = Synchronize(_board, turn);
        _board = board;
        GameView.OpponentMoved(ply, LastMove(turn), board, clock);
        bot.TakeReport();
        var choice = Guard.Call("ChooseMove", () => bot.ChooseMove(board.Copy(), clock));
        var report = bot.TakeReport();
        if (choice == Move.Resign)
        {
            channel.Send(Protocol.Resign);
            return;
        }
        string uci;
        try
        {
            uci = choice.Uci();
        }
        catch (ChessException)
        {
            throw new BotFailureException($"ChooseMove returned {choice}, which has no UCI form");
        }
        var info = report is null ? null : InfoFields.Json(report);
        channel.Send(json => Protocol.Move(json, uci, info));
        try
        {
            board.MakeMove(choice);
        }
        catch (ChessException)
        {
            Log.Warn($"own move {uci} is not legal in this position; the referee decides");
            return;
        }
        GameView.OwnMove(ply + 1, uci, board, clock, info);
    }

    /// <summary>Applies the opponent's move and adopts the referee's position on a mismatch (E42).</summary>
    private static Board Synchronize(Board board, JsonElement turn)
    {
        var fen = Protocol.String(turn, "fen");
        Board reference;
        try
        {
            // Read and written again, so an en passant square without a legal capture still
            // compares equal (E48).
            reference = Board.FromFen(fen);
        }
        catch (ChessException error)
        {
            throw new ProtocolException($"turn: {error.Message}");
        }
        if (LastMove(turn) is { } lastMove)
        {
            // A move that does not fit is repaired by the comparison below.
            try
            {
                board.MakeMove(board.ParseMove(lastMove));
            }
            catch (ChessException) { }
        }
        if (board.Fen() != reference.Fen())
        {
            Log.Warn($"own position differs from the referee's; continuing from {fen}");
            return reference;
        }
        return board;
    }

    private void End(JsonElement gameOver)
    {
        var result = Protocol.GameResult(gameOver);
        Result = result;
        GameView.Ended(gameOver);
        Guard.Call("OnGameEnd", () => bot.OnGameEnd(result));
    }

    private static string? LastMove(JsonElement turn) =>
        turn.TryGetProperty("last_move", out var lastMove)
        && lastMove.ValueKind == JsonValueKind.String
            ? lastMove.GetString()
            : null;

    private static string Text(JsonElement message, string name) =>
        message.TryGetProperty(name, out var value) && value.ValueKind == JsonValueKind.String
            ? value.GetString()!
            : Protocol.Json(message, name);
}
