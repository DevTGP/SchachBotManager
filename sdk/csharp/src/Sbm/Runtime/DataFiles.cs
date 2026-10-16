namespace Sbm.Runtime;

/// <summary>The data files uploaded with the bot (spec/api/runtime.json, E30, E62).</summary>
internal static class DataFiles
{
    internal const string DirectoryVariable = "SBM_DATA_DIR";

    /// <summary>SBM_DATA_DIR if set (server), otherwise the directory data next to the program.</summary>
    internal static string Directory(Func<string, string?> env)
    {
        var configured = env(DirectoryVariable);
        return string.IsNullOrEmpty(configured)
            ? Path.Combine(AppContext.BaseDirectory, "data")
            : configured;
    }

    internal static byte[] Load(string name, string directory)
    {
        ArgumentNullException.ThrowIfNull(name);
        if (!IsPlainName(name))
        {
            throw new InvalidArgumentException(
                $"Sdk.LoadData: {Native.Text.Quote(name)} is not a plain file name"
            );
        }
        var path = Path.Combine(directory, name);
        if (!File.Exists(path))
        {
            throw new DataNotFoundException(
                $"Sdk.LoadData: no data file {Native.Text.Quote(name)} in {directory}"
            );
        }
        return File.ReadAllBytes(path);
    }

    private static bool IsPlainName(string name) =>
        name is not ("" or "." or "..")
        && name.IndexOfAny(['/', '\\', '\0']) < 0
        // Catches what the platform reads as a path anyway, e.g. C:book.bin on Windows.
        && Path.GetFileName(name) == name
        && string.IsNullOrEmpty(Path.GetPathRoot(name));
}
