namespace Sbm.Tests.Runtime;

/// <summary>Tests that write the log or the console, which are shared by the whole process.</summary>
[CollectionDefinition(Name, DisableParallelization = true)]
public sealed class SharedLog
{
    public const string Name = "Log";
}
