using System.Text;

namespace Sbm.Runtime.Play;

/// <summary>
/// Splits a command line into words. posix follows a POSIX shell like shlex in the Python SDK:
/// single and double quotes group, a backslash escapes the next character, inside double quotes
/// only a double quote or a backslash. Otherwise, as on Windows, only double quotes group and
/// backslashes stay, so paths like C:\bots\engine.exe keep working.
/// </summary>
internal static class CommandLine
{
    private const string Whitespace = " \t\r\n";

    /// <summary>Throws FormatException for an open quote or a backslash at the end.</summary>
    internal static IReadOnlyList<string> Split(string text, bool posix)
    {
        var words = new List<string>();
        var word = new StringBuilder();
        var inWord = false;
        var index = 0;
        while (index < text.Length)
        {
            var c = text[index];
            if (Whitespace.Contains(c, StringComparison.Ordinal))
            {
                if (inWord)
                {
                    words.Add(word.ToString());
                    word.Clear();
                    inWord = false;
                }
                index++;
                continue;
            }
            inWord = true;
            if (c == '"' || (posix && c == '\''))
            {
                index = Quoted(text, index + 1, c, posix, word);
            }
            else if (posix && c == '\\')
            {
                word.Append(Escaped(text, index + 1));
                index += 2;
            }
            else
            {
                word.Append(c);
                index++;
            }
        }
        if (inWord)
        {
            words.Add(word.ToString());
        }
        return words;
    }

    /// <summary>Appends the quoted text from start; returns the index after the closing quote.</summary>
    private static int Quoted(string text, int start, char quote, bool posix, StringBuilder word)
    {
        var index = start;
        while (index < text.Length)
        {
            var c = text[index];
            if (c == quote)
            {
                return index + 1;
            }
            if (posix && quote == '"' && c == '\\')
            {
                var next = Escaped(text, index + 1);
                if (next is not ('"' or '\\'))
                {
                    word.Append('\\');
                }
                word.Append(next);
                index += 2;
                continue;
            }
            word.Append(c);
            index++;
        }
        throw new FormatException("No closing quotation");
    }

    private static char Escaped(string text, int index) =>
        index < text.Length ? text[index] : throw new FormatException("No escaped character");
}
