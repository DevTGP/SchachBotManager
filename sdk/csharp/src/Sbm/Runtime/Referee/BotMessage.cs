namespace Sbm.Runtime.Referee;

/// <summary>A message from a bot to the referee after the strict check (E66).</summary>
internal abstract record BotMessage;

/// <summary>The bot has started; sdk is a SemVer version, lang one of the five languages.</summary>
internal sealed record ReadyMessage(string Sdk, string Lang) : BotMessage;

/// <summary>A move in UCI notation; the info fields are checked but not kept.</summary>
internal sealed record MoveMessage(string Uci) : BotMessage;

/// <summary>The bot gives up.</summary>
internal sealed record ResignMessage : BotMessage;
