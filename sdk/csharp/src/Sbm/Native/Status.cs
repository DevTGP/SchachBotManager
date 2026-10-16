namespace Sbm.Native;

/// <summary>Status codes of status.h as exceptions of the SDK (E49, E52).</summary>
internal static class Status
{
    internal const int Ok = 0;
    internal const int InvalidArgument = 1;
    internal const int InvalidFen = 2;
    internal const int InvalidUci = 3;
    internal const int IllegalMove = 4;
    internal const int InvalidState = 5;
    internal const int OutOfMemory = 7;

    /// <summary>Throws the exception for a status other than SBM_OK.</summary>
    /// <param name="status">Status returned by the core.</param>
    /// <param name="what">Call named at the start of the message, e.g. <c>Board.MakeMove</c>.</param>
    internal static void Check(int status, string what)
    {
        if (status != Ok)
        {
            throw Error(status, what);
        }
    }

    internal static Exception Error(int status, string what) =>
        status switch
        {
            InvalidArgument => new InvalidArgumentException($"{what}: invalid argument"),
            InvalidFen => new InvalidFenException($"{what}: invalid FEN"),
            InvalidUci => new InvalidUciException($"{what}: not a move in UCI notation"),
            IllegalMove => new IllegalMoveException($"{what}: illegal move"),
            InvalidState => new InvalidStateException($"{what}: not possible in the current state"),
            OutOfMemory => new InsufficientMemoryException($"{what}: out of memory"),
            // SBM_BUFFER_TOO_SMALL and SBM_INTERNAL_ERROR are bugs of the binding or the core.
            _ => new ChessException($"{what}: internal error ({Text.Name(status)})"),
        };
}
