namespace Sbm;

/// <summary>
/// Search information sent with the move (E43) and shown publicly in the viewer; every field is
/// optional. The SDK truncates Pv to 32 moves and Text to 256 characters and leaves out other
/// fields outside the protocol limits with a warning (E63).
/// </summary>
public sealed record Info
{
    /// <summary>Search depth, 0 to 1024.</summary>
    public int? Depth { get; init; }

    /// <summary>Selective search depth, 0 to 1024.</summary>
    public int? Seldepth { get; init; }

    /// <summary>Score in centipawns from the bot's point of view; not together with ScoreMate.</summary>
    public int? ScoreCp { get; init; }

    /// <summary>Mate in this many moves, negative if the bot gets mated; not 0.</summary>
    public int? ScoreMate { get; init; }

    /// <summary>Searched nodes.</summary>
    public long? Nodes { get; init; }

    /// <summary>Principal variation starting with the move played.</summary>
    public IReadOnlyList<Move>? Pv { get; init; }

    /// <summary>Free text.</summary>
    public string? Text { get; init; }
}
