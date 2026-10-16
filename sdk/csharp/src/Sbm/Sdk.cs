using Sbm.Native;

namespace Sbm;

/// <summary>Information about the SDK.</summary>
public static class Sdk
{
    /// <summary>Semantic version of the core, equal to the SDK version (E36).</summary>
    public static string Version { get; } = ReadVersion();

    private static unsafe string ReadVersion() => Text.FromC(Core.sbm_version());
}
