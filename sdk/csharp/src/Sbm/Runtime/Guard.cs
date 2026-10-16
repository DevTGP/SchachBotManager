using System.Reflection;

namespace Sbm.Runtime;

/// <summary>Calls bot code and turns any exception into a BotFailureException that keeps it.</summary>
internal static class Guard
{
    internal static T Call<T>(string name, Func<T> callback)
    {
        try
        {
            return callback();
        }
        // Bot code may throw anything; it ends the game with the exception in the log (E49).
#pragma warning disable CA1031
        catch (Exception error)
#pragma warning restore CA1031
        {
            // new TBot() reports an exception of the constructor wrapped in this one.
            var cause = error is TargetInvocationException { InnerException: { } inner }
                ? inner
                : error;
            throw new BotFailureException(
                $"{name} raised {cause.GetType().Name}: {cause.Message}",
                cause
            );
        }
    }

    internal static void Call(string name, Action callback) =>
        Call<object?>(
            name,
            () =>
            {
                callback();
                return null;
            }
        );

    /// <summary>The message with the stack trace of the bot's exception, for the log.</summary>
    internal static string Describe(BotFailureException error) =>
        error.InnerException is { } cause
            ? $"{error.Message}\n{cause.ToString().TrimEnd()}"
            : error.Message;
}
