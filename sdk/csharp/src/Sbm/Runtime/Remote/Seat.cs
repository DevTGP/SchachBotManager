namespace Sbm.Runtime.Remote;

/// <summary>The seat the web API gave for a remote game: the token to join it and where.</summary>
internal sealed record Seat(string MatchId, string Token, string Color, string SocketUrl);
