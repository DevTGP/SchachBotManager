namespace Sbm.Build.Tests;

/// <summary>Files of the repository, found from the test's output folder.</summary>
internal static class Repository
{
    public static string Root { get; } = Find();

    public static string Path(string relative) => System.IO.Path.Combine(Root, relative);

    private static string Find()
    {
        for (
            var dir = new DirectoryInfo(AppContext.BaseDirectory);
            dir is not null;
            dir = dir.Parent
        )
        {
            if (File.Exists(System.IO.Path.Combine(dir.FullName, "sdk", "csharp", "Sbm.slnx")))
            {
                return dir.FullName;
            }
        }
        throw new InvalidOperationException("the repository root was not found");
    }
}
