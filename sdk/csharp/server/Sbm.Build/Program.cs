using Sbm.Analyzers;

namespace Sbm.Build;

/// <summary>
/// sbm-build: exit code 0 with the program, 1 with findings, 2 for a wrong command line; any
/// other code or a crash is a failure of the tool. The report goes to stdout (Report).
/// </summary>
internal static class Program
{
    private static int Main(string[] args)
    {
        var options = Options.Parse(args, out var error);
        if (options is null)
        {
            Console.Error.WriteLine($"sbm-build: {error}");
            return 2;
        }
        var result = BotBuild.Run(options, RuleSet.Default);
        using (var stdout = Console.OpenStandardOutput())
        {
            Report.Write(stdout, result);
        }
        return result.Ok ? 0 : 1;
    }
}
