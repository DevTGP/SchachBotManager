using System.Runtime.InteropServices;

namespace Sbm.Native;

/// <summary>
/// Functions of the flat C interface of the core (sdk/core/include/sbm/), one file per header.
/// Every function returns a status code of status.h; results go through out-pointers.
/// </summary>
internal static unsafe partial class Core
{
    internal const string Library = "sbm";

    /// <summary>SBM_ABI_VERSION of the headers this binding was written against.</summary>
    internal const int AbiVersion = 1;

    static Core()
    {
        var loaded = sbm_abi_version();
        if (loaded != AbiVersion)
        {
            throw new InvalidOperationException(
                $"Sbm: the native library has ABI version {loaded}, the SDK needs {AbiVersion}"
            );
        }
    }

    [LibraryImport(Library)]
    private static partial int sbm_abi_version();

    [LibraryImport(Library)]
    internal static partial byte* sbm_version();

    [LibraryImport(Library)]
    internal static partial byte* sbm_status_name(int status);
}
