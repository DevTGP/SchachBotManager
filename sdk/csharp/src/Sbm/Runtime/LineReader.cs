namespace Sbm.Runtime;

/// <summary>Reads lines of bytes up to <c>\n</c>, with a limit on their length.</summary>
internal sealed class LineReader(Stream stream)
{
    private readonly byte[] _buffer = new byte[4096];
    private int _start;
    private int _end;

    /// <summary>
    /// The next line without <c>\n</c> and a trailing <c>\r</c>, or null at the end of the
    /// input; a last line without <c>\n</c> counts as a line.
    /// </summary>
    public byte[]? ReadLine(int maxBytes)
    {
        var line = new MemoryStream();
        while (true)
        {
            if (_start == _end && !Fill())
            {
                return line.Length == 0 ? null : Finish(line, maxBytes);
            }
            var span = _buffer.AsSpan(_start, _end - _start);
            var newline = span.IndexOf((byte)'\n');
            var take = newline < 0 ? span.Length : newline;
            line.Write(span[..take]);
            _start += newline < 0 ? take : take + 1;
            // One byte of room for a \r before the \n.
            if (line.Length > maxBytes + 1)
            {
                throw new ProtocolException($"line longer than {maxBytes} bytes");
            }
            if (newline >= 0)
            {
                return Finish(line, maxBytes);
            }
        }
    }

    private bool Fill()
    {
        _start = 0;
        _end = stream.Read(_buffer, 0, _buffer.Length);
        return _end > 0;
    }

    private static byte[] Finish(MemoryStream line, int maxBytes)
    {
        var content = line.ToArray();
        if (content.Length > 0 && content[^1] == (byte)'\r')
        {
            content = content[..^1];
        }
        return content.Length > maxBytes
            ? throw new ProtocolException($"line longer than {maxBytes} bytes")
            : content;
    }
}
