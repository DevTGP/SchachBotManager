using Sbm.Runtime;

namespace Sbm;

public static partial class Sdk
{
    /// <summary>
    /// Contents of a data file uploaded with the bot (E30); the only way for a bot to read files.
    /// Reads from the directory named by SBM_DATA_DIR, which the server sets, otherwise from the
    /// directory data next to the program (E62).
    /// </summary>
    /// <param name="name">File name without directory, as uploaded.</param>
    /// <exception cref="InvalidArgumentException">The name is not a plain file name.</exception>
    /// <exception cref="DataNotFoundException">There is no data file with that name.</exception>
    public static byte[] LoadData(string name) =>
        DataFiles.Load(name, DataFiles.Directory(Environment.GetEnvironmentVariable));
}
