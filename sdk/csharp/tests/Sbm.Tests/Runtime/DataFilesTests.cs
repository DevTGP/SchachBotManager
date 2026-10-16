using Sbm.Runtime;

namespace Sbm.Tests.Runtime;

/// <summary>Sdk.LoadData: plain file names in the data directory (E62).</summary>
public sealed class DataFilesTests : IDisposable
{
    private readonly DirectoryInfo _dir = Directory.CreateTempSubdirectory("sbm-data-");

    public DataFilesTests() =>
        File.WriteAllBytes(Path.Combine(_dir.FullName, "book.bin"), [0, 1, 2, 255]);

    public void Dispose() => _dir.Delete(recursive: true);

    [Fact]
    public void ReadsBytes() =>
        Assert.Equal([0, 1, 2, 255], DataFiles.Load("book.bin", _dir.FullName));

    [Theory]
    [InlineData("")]
    [InlineData(".")]
    [InlineData("..")]
    [InlineData("../book.bin")]
    [InlineData("sub/book.bin")]
    [InlineData("sub\\book.bin")]
    [InlineData("/etc/passwd")]
    [InlineData("C:book.bin")]
    [InlineData("book.bin\0")]
    public void RejectsPaths(string name)
    {
        if (name == "C:book.bin" && !OperatingSystem.IsWindows())
        {
            // Only Windows reads it as a path; elsewhere it is a plain, missing name.
            Assert.Throws<DataNotFoundException>(() => DataFiles.Load(name, _dir.FullName));
            return;
        }
        var error = Assert.Throws<InvalidArgumentException>(() =>
            DataFiles.Load(name, _dir.FullName)
        );
        Assert.Contains("is not a plain file name", error.Message, StringComparison.Ordinal);
    }

    [Fact]
    public void MissingFile()
    {
        var error = Assert.Throws<DataNotFoundException>(() =>
            DataFiles.Load("missing.bin", _dir.FullName)
        );
        Assert.Equal(
            $"Sdk.LoadData: no data file \"missing.bin\" in {_dir.FullName}",
            error.Message
        );
    }

    [Fact]
    public void NullName() =>
        Assert.Throws<ArgumentNullException>(() => DataFiles.Load(null!, _dir.FullName));

    [Fact]
    public void DirectoryFromTheEnvironment()
    {
        Assert.Equal("/data", DataFiles.Directory(name => name == "SBM_DATA_DIR" ? "/data" : null));
        Assert.Equal(
            Path.Combine(AppContext.BaseDirectory, "data"),
            DataFiles.Directory(_ => null)
        );
        Assert.Equal(Path.Combine(AppContext.BaseDirectory, "data"), DataFiles.Directory(_ => ""));
    }
}
