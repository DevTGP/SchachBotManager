namespace Sbm.Runtime.Play;

/// <summary>The arguments of Sdk.Play besides the bot class (spec/api/runtime.json).</summary>
internal sealed record PlayRequest(string Opponent)
{
    public string? Server { get; init; }

    public string? Token { get; init; }

    public string Color { get; init; } = "random";

    public string? Time { get; init; }

    public string? Discipline { get; init; }

    public int Games { get; init; } = 1;

    public bool Viewer { get; init; }
}
