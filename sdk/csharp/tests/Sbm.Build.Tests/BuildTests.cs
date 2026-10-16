using System.Reflection.Metadata;
using System.Reflection.Metadata.Ecma335;
using System.Reflection.PortableExecutable;

namespace Sbm.Build.Tests;

public class BuildTests
{
    [Fact]
    public void The_template_builds()
    {
        using var bot = new Workspace()
            .Add(
                "TemplateBot.cs",
                File.ReadAllBytes(Repository.Path("templates/csharp/TemplateBot.cs"))
            )
            .Add(
                "data/book.txt",
                File.ReadAllBytes(Repository.Path("templates/csharp/data/book.txt"))
            );

        var result = bot.Build("MyBot.TemplateBot");

        Assert.Empty(result.Analysis.Findings);
        Assert.True(result.Ok);
        Assert.Equal("Sbm.Generated.Entry", EntryType(result.Program!));
    }

    [Fact]
    public void The_reference_bot_builds()
    {
        using var bot = new Workspace().Add(
            "MaterialBot.cs",
            File.ReadAllBytes(Repository.Path("sdk/csharp/bots/Material/MaterialBot.cs"))
        );

        var result = bot.Build("Sbm.Bots.MaterialBot");

        Assert.True(
            result.Ok,
            string.Join("\n", result.Build?.Findings ?? result.Analysis.Findings)
        );
    }

    [Fact]
    public void Common_language_features_build_with_the_allowed_references()
    {
        const string members = """
                private readonly Queue<int> _queue = new();
                private readonly Stack<string> _stack = new();
                public int Depth { get; init; } = 1;

                private record Entry(ulong Key, int Score);

                public int Features()
                {
                    int[] values = [3, 1, 2];
                    var (low, high) = (values.Min(), values[^1]);
                    var sorted = values.OrderBy(v => v).Where(v => v > low).ToArray()[0..1];
                    var map = new Dictionary<string, Entry> { ["a"] = new(1UL, high) };
                    var set = new HashSet<int>(values);
                    _queue.Enqueue(sorted.Length);
                    _stack.Push($"{map["a"].Score:D3}");
                    ReadOnlySpan<byte> bytes = "e2e4"u8;
                    return bytes.Length + set.Count + _queue.Peek() + _stack.Peek().Length + Depth;
                }
            """;
        using var bot = new Workspace().Add("Bot.cs", Text.Bot(members));

        var result = bot.Build();

        Assert.True(
            result.Ok,
            string.Join("\n", result.Build?.Findings ?? result.Analysis.Findings)
        );
    }

    [Fact]
    public void A_bot_class_in_a_nested_namespace_builds()
    {
        using var bot = new Workspace().Add(
            "Engine/Bot.cs",
            "namespace Team.Engine.V2;\n\n" + Text.Bot()
        );

        Assert.True(bot.Build("Team.Engine.V2.TestBot").Ok);
    }

    [Fact]
    public void Files_in_the_data_folder_are_not_compiled()
    {
        using var bot = new Workspace()
            .Add("Bot.cs", Text.Bot())
            .Add("data/Broken.cs", "this is no C#");

        Assert.True(bot.Build().Ok);
    }

    [Fact]
    public void A_byte_order_mark_is_accepted()
    {
        using var bot = new Workspace().Add(
            "Bot.cs",
            [0xEF, 0xBB, 0xBF, .. Text.Encode(Text.Bot())]
        );

        Assert.True(bot.Build().Ok);
    }

    [Fact]
    public void A_compile_error_gives_no_program()
    {
        using var bot = new Workspace().Add("Bot.cs", Text.Bot("int M() => \"no int\";"));

        var result = bot.Build();

        Assert.True(result.Analysis.Ok);
        var finding = Assert.Single(result.Build!.Findings);
        Assert.Equal("CS0029", finding.Rule);
        Assert.Equal("Bot.cs", finding.File);
        Assert.Null(result.Program);
    }

    [Fact]
    public void The_build_is_deterministic()
    {
        using var bot = new Workspace().Add("Bot.cs", Text.Bot());

        Assert.Equal(bot.Build().Program, bot.Build().Program);
    }

    private static string EntryType(byte[] program)
    {
        using var pe = new PEReader(new MemoryStream(program));
        var metadata = pe.GetMetadataReader();
        var token = pe.PEHeaders.CorHeader!.EntryPointTokenOrRelativeVirtualAddress;
        var method = metadata.GetMethodDefinition(
            MetadataTokens.MethodDefinitionHandle(token & 0xFFFFFF)
        );
        var type = metadata.GetTypeDefinition(method.GetDeclaringType());
        return $"{metadata.GetString(type.Namespace)}.{metadata.GetString(type.Name)}";
    }
}
