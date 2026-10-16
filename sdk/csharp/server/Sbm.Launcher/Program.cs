using System.Reflection;
using System.Runtime.Loader;
using System.Text.Json;

namespace Sbm.Launcher;

/// <summary>
/// Starts the program of a C# bot (E204): reads the file SBM_PROGRAM names into memory, loads it
/// next to the SDK and runs its entry point, which the build tool generated as Sdk.Run of the bot
/// class. The program only references the SDK and the framework, both of which this launcher
/// brings; the command line passes through to Sdk.Run. With --versions it prints the versions of
/// .NET and the SDK instead, the self-check of the runner.
/// </summary>
internal static class Program
{
    private const string ProgramVariable = "SBM_PROGRAM";

    private static int Main(string[] args)
    {
        if (args is ["--versions"])
        {
            Console.WriteLine(Versions());
            return 0;
        }
        var path = Environment.GetEnvironmentVariable(ProgramVariable);
        if (string.IsNullOrEmpty(path))
        {
            Console.Error.WriteLine($"sbm-launch: {ProgramVariable} is not set");
            return 2;
        }
        // From memory, not from the file: the bot directory is mounted without exec.
        using var image = new MemoryStream(File.ReadAllBytes(path));
        var assembly = AssemblyLoadContext.Default.LoadFromStream(image);
        var entry =
            assembly.EntryPoint
            ?? throw new InvalidOperationException($"the program {path} has no entry point");
        object?[]? parameters = entry.GetParameters().Length == 0 ? null : [args];
        var result = entry.Invoke(null, BindingFlags.DoNotWrapExceptions, null, parameters, null);
        return result is int code ? code : 0;
    }

    private static string Versions() =>
        JsonSerializer.Serialize(
            new Dictionary<string, string>
            {
                ["dotnet"] = Environment.Version.ToString(),
                ["sdk"] = Sdk.Version,
            }
        );
}
