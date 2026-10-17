using System.Text.RegularExpressions;
using Sbm.Runtime.Viewer;

namespace Sbm.Tests.Runtime.Viewer;

public sealed partial class ViewerProgramTests
{
    [Fact]
    public void RuntimeIdentifierIsPortable() =>
        Assert.Matches(PortableIdentifier(), ViewerProgram.RuntimeIdentifier());

    [Fact]
    public void ProgramLiesInTheFolderOfThePlatform()
    {
        // The tests copy the core flat next to the assembly, but not the viewer.
        Assert.SkipWhen(
            File.Exists(Path.Combine(AppContext.BaseDirectory, ViewerProgram.Name)),
            "the viewer lies next to the tests"
        );
        var expected = Path.Combine(
            AppContext.BaseDirectory,
            "runtimes",
            ViewerProgram.RuntimeIdentifier(),
            "native",
            ViewerProgram.Name
        );
        Assert.Equal(expected, ViewerProgram.Path());
    }

    [GeneratedRegex("^(win|osx|linux)-(x64|arm64)$")]
    private static partial Regex PortableIdentifier();
}
